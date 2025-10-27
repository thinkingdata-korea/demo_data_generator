"""
Rate limiter for AI API calls.
Inspired by Metabase dataset-generator's rate limiting strategy.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class RateLimiter:
    """AI API 호출 rate limiting"""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Args:
            max_requests: 최대 요청 수
            window_seconds: 시간 윈도우 (초)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)

    def check_limit(self, identifier: str = 'default') -> bool:
        """
        Rate limit 체크

        Args:
            identifier: 식별자 (예: "openai", "anthropic")

        Returns:
            True if allowed, raises Exception if rate limited

        Raises:
            Exception: Rate limit 초과 시
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # 이전 요청 기록 정리 (윈도우 밖의 요청 제거)
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]

        # Rate limit 체크
        if len(self.requests[identifier]) >= self.max_requests:
            oldest = self.requests[identifier][0]
            wait_time = (oldest + timedelta(seconds=self.window_seconds) - now).total_seconds()

            if wait_time > 0:
                raise Exception(
                    f"Rate limit exceeded: {len(self.requests[identifier])}/{self.max_requests} "
                    f"requests in {self.window_seconds}s. Wait {wait_time:.1f}s"
                )

        # 요청 기록
        self.requests[identifier].append(now)
        return True

    def wait_if_needed(self, identifier: str = 'default', verbose: bool = True):
        """
        필요시 자동 대기

        Args:
            identifier: 식별자
            verbose: 대기 메시지 출력 여부
        """
        while True:
            try:
                self.check_limit(identifier)
                break
            except Exception as e:
                if "Rate limit" in str(e):
                    # Wait time 추출
                    wait_time = float(str(e).split('Wait ')[1].split('s')[0])

                    if verbose:
                        print(f"  ⏳ Rate limit 도달. {wait_time:.1f}초 대기 중...")

                    time.sleep(wait_time + 0.5)  # 약간 여유 시간 추가
                else:
                    raise

    def get_stats(self, identifier: str = 'default') -> Dict:
        """
        현재 rate limit 통계

        Args:
            identifier: 식별자

        Returns:
            통계 딕셔너리
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # 현재 윈도우 내의 요청만 카운트
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]

        remaining = max(0, self.max_requests - len(recent_requests))

        return {
            'identifier': identifier,
            'max_requests': self.max_requests,
            'window_seconds': self.window_seconds,
            'current_count': len(recent_requests),
            'remaining': remaining,
            'usage_percent': (len(recent_requests) / self.max_requests * 100) if self.max_requests > 0 else 0
        }

    def reset(self, identifier: Optional[str] = None):
        """
        Rate limit 리셋

        Args:
            identifier: 특정 식별자만 리셋 (None이면 전체)
        """
        if identifier:
            self.requests[identifier] = []
        else:
            self.requests.clear()
