"""
LogBus2 설정 파일 생성 모듈
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class LogBusDataSource:
    """LogBus2 데이터 소스 설정"""
    file_patterns: List[str]
    app_id: str
    type: str = "file"
    unit_remove: Optional[str] = None  # "day" or "hour"
    offset_remove: Optional[int] = None
    remove_dirs: bool = False
    http_compress: str = "gzip"  # "none" or "gzip"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        config = {
            "type": self.type,
            "file_patterns": self.file_patterns,
            "app_id": self.app_id,
            "http_compress": self.http_compress,
        }

        if self.unit_remove:
            config["unit_remove"] = self.unit_remove
        if self.offset_remove is not None and self.offset_remove > 0:
            config["offset_remove"] = self.offset_remove
        if self.remove_dirs:
            config["remove_dirs"] = self.remove_dirs

        return config


@dataclass
class LogBusConfig:
    """LogBus2 전체 설정"""
    push_url: str
    datasources: List[LogBusDataSource] = field(default_factory=list)
    cpu_limit: Optional[int] = None
    min_disk_free_space: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        config = {
            "push_url": self.push_url,
            "datasource": [ds.to_dict() for ds in self.datasources]
        }

        if self.cpu_limit:
            config["cpu_limit"] = self.cpu_limit
        if self.min_disk_free_space:
            config["min_disk_free_space"] = self.min_disk_free_space

        return config

    def save(self, output_path: Path) -> Path:
        """설정 파일 저장"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        return output_path


class LogBusConfigGenerator:
    """LogBus2 설정 파일 생성기"""

    @staticmethod
    def create_config(
        data_file_path: str,
        app_id: str,
        push_url: str,
        cpu_limit: Optional[int] = 4,
        http_compress: str = "gzip",
        auto_remove: bool = False,
        remove_after_days: int = 7
    ) -> LogBusConfig:
        """
        생성된 데이터 파일을 위한 LogBus 설정 생성

        Args:
            data_file_path: 생성된 데이터 파일 경로 (절대 경로)
            app_id: ThinkingEngine APP ID
            push_url: ThinkingEngine Receiver URL
            cpu_limit: CPU 코어 수 제한
            http_compress: HTTP 압축 방식 ("none" or "gzip")
            auto_remove: 파일 자동 삭제 여부
            remove_after_days: 파일 삭제 기간 (일)
        """
        # 파일 경로를 glob 패턴으로 변환
        file_path = Path(data_file_path)
        if file_path.is_file():
            # 특정 파일인 경우 해당 파일만
            pattern = str(file_path.absolute())
        else:
            # 디렉터리인 경우 *.jsonl 패턴
            pattern = str(file_path.absolute() / "*.jsonl")

        datasource = LogBusDataSource(
            file_patterns=[pattern],
            app_id=app_id,
            http_compress=http_compress,
            unit_remove="day" if auto_remove else None,
            offset_remove=remove_after_days if auto_remove else None,
            remove_dirs=False
        )

        config = LogBusConfig(
            push_url=push_url,
            datasources=[datasource],
            cpu_limit=cpu_limit
        )

        return config

    @staticmethod
    def create_config_for_directory(
        data_dir: str,
        app_id: str,
        push_url: str,
        file_pattern: str = "*.jsonl",
        cpu_limit: Optional[int] = 4,
        http_compress: str = "gzip",
        auto_remove: bool = False,
        remove_after_days: int = 7,
        remove_dirs: bool = False
    ) -> LogBusConfig:
        """
        디렉터리 내 모든 파일을 위한 LogBus 설정 생성

        Args:
            data_dir: 데이터 파일이 있는 디렉터리 경로
            app_id: ThinkingEngine APP ID
            push_url: ThinkingEngine Receiver URL
            file_pattern: 파일 매칭 패턴 (예: "*.jsonl", "logs_*.jsonl")
            cpu_limit: CPU 코어 수 제한
            http_compress: HTTP 압축 방식
            auto_remove: 파일 자동 삭제 여부
            remove_after_days: 파일 삭제 기간 (일)
            remove_dirs: 디렉터리 자동 삭제 여부
        """
        dir_path = Path(data_dir).absolute()
        pattern = str(dir_path / file_pattern)

        datasource = LogBusDataSource(
            file_patterns=[pattern],
            app_id=app_id,
            http_compress=http_compress,
            unit_remove="day" if auto_remove else None,
            offset_remove=remove_after_days if auto_remove else None,
            remove_dirs=remove_dirs
        )

        config = LogBusConfig(
            push_url=push_url,
            datasources=[datasource],
            cpu_limit=cpu_limit
        )

        return config
