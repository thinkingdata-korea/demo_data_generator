"""
Cache manager for AI analysis results.
Inspired by Metabase dataset-generator's caching strategy.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class CacheManager:
    """AI 분석 결과 캐시 관리"""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def compute_taxonomy_hash(self, taxonomy_properties: list) -> str:
        """택소노미 해시 계산 (캐시 키 생성용)"""
        # 속성 이름과 타입으로 해시 생성
        content = json.dumps(
            sorted([
                (prop.get('name'), prop.get('property_type'))
                for prop in taxonomy_properties
            ]),
            sort_keys=True
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_cache_key(self, taxonomy_hash: str, ai_provider: str, product_info: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 택소노미 + AI provider + industry로 캐시 키 생성
        industry = product_info.get('industry', 'unknown')
        platform = product_info.get('platform', 'unknown')
        return f"{ai_provider}_{industry}_{platform}_{taxonomy_hash}"

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시 로드"""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                created_at = data.get('created_at', 'unknown')
                print(f"  ✓ 캐시된 AI 분석 결과 사용 (생성일: {created_at})")
                return data.get('rules')
        except Exception as e:
            print(f"  ⚠️  캐시 로드 실패: {e}")
            return None

    def save(self, key: str, rules: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """캐시 저장"""
        cache_file = self.cache_dir / f"{key}.json"

        cache_data = {
            'created_at': datetime.now().isoformat(),
            'rules': rules,
            'metadata': metadata or {}
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"  ✓ AI 분석 결과 캐시 저장")
        except Exception as e:
            print(f"  ⚠️  캐시 저장 실패: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        cache_files = list(self.cache_dir.glob("*.json"))

        if not cache_files:
            return {
                'total_cached': 0,
                'total_size_mb': 0,
                'cache_dir': str(self.cache_dir),
                'files': []
            }

        total_size = sum(f.stat().st_size for f in cache_files)

        files_info = []
        for f in sorted(cache_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    created = data.get('created_at', 'unknown')
            except:
                created = 'unknown'

            files_info.append({
                'name': f.name,
                'size_kb': round(f.stat().st_size / 1024, 2),
                'created': created,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })

        return {
            'total_cached': len(cache_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'cache_dir': str(self.cache_dir.absolute()),
            'files': files_info
        }

    def clear(self, pattern: Optional[str] = None):
        """캐시 초기화"""
        if pattern:
            # 특정 패턴만 삭제
            files = list(self.cache_dir.glob(f"*{pattern}*.json"))
            for cache_file in files:
                cache_file.unlink()
            print(f"  ✓ 캐시 {len(files)}개 파일 삭제 (패턴: {pattern})")
        else:
            # 전체 삭제
            files = list(self.cache_dir.glob("*.json"))
            for cache_file in files:
                cache_file.unlink()
            print(f"  ✓ 전체 캐시 초기화 완료 ({len(files)}개 파일)")

    def exists(self, key: str) -> bool:
        """캐시 존재 여부 확인"""
        cache_file = self.cache_dir / f"{key}.json"
        return cache_file.exists()
