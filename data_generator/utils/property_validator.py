"""
ThinkingEngine 속성명 검증 및 정제 유틸리티
"""
import re
from typing import Dict, Any, Set


class PropertyNameValidator:
    """
    ThinkingEngine 속성명 규칙:
    1. 숫자나 문자로 시작해야 함
    2. 숫자, 문자, 밑줄(_)만 포함 가능
    3. 최대 길이 50자
    4. "#"으로 시작하는 속성은 미리 설정된 속성만 가능
    """

    # 미리 설정된 ThinkingEngine 속성 (# 시작 가능)
    PREDEFINED_PROPERTIES = {
        # 시스템 필드
        '#type', '#time', '#event_name', '#account_id', '#distinct_id', '#uuid',
        # 기본 공통 속성
        '#ip', '#country', '#country_code', '#province', '#city', '#lib', '#lib_version',
        '#zone_offset', '#device_id', '#screen_height', '#screen_width', '#system_language',
        # 플랫폼별 속성
        '#os', '#os_version', '#device_model', '#device_type', '#manufacturer',
        '#app_version', '#bundle_id', '#network_type', '#carrier', '#install_time',
        '#simulator', '#ram', '#disk', '#fps',
        '#browser', '#browser_version', '#ua', '#utm',
        # 이벤트별 전용 속성
        '#resume_from_background', '#background_duration', '#start_reason',  # ta_app_start
        '#duration',  # ta_app_end
        '#title', '#screen_name', '#url', '#url_path', '#referrer', '#referrer_host',  # ta_app_view
        '#element_id', '#element_type', '#element_selector', '#element_position', '#element_content',  # ta_app_click
        '#app_crashed_reason',  # ta_app_crash
    }

    # 속성명 검증 패턴: 숫자/문자로 시작, 숫자/문자/밑줄만 포함
    VALID_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_]{0,49}$')

    @classmethod
    def is_valid_property_name(cls, name: str) -> bool:
        """
        속성명이 유효한지 검증

        Args:
            name: 속성명

        Returns:
            유효 여부
        """
        # 미리 설정된 속성 (#로 시작)
        if name.startswith('#'):
            return name in cls.PREDEFINED_PROPERTIES

        # 일반 속성
        return bool(cls.VALID_PATTERN.match(name))

    @classmethod
    def sanitize_property_name(cls, name: str) -> str:
        """
        속성명을 ThinkingEngine 규칙에 맞게 정제

        Args:
            name: 원본 속성명

        Returns:
            정제된 속성명
        """
        # 미리 설정된 속성은 그대로 반환
        if name.startswith('#') and name in cls.PREDEFINED_PROPERTIES:
            return name

        # # 제거 (미리 설정된 속성이 아닌 경우)
        if name.startswith('#'):
            name = name[1:]

        # 점(.)을 밑줄(_)로 변환
        name = name.replace('.', '_')

        # 하이픈(-)을 밑줄(_)로 변환
        name = name.replace('-', '_')

        # 공백을 밑줄(_)로 변환
        name = name.replace(' ', '_')

        # 허용되지 않는 문자 제거
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)

        # 숫자로 시작하면 앞에 밑줄 추가
        if name and name[0].isdigit():
            name = '_' + name

        # 밑줄로 시작하면서 그 다음이 없는 경우 처리
        if not name or name == '_':
            name = 'property_' + name

        # 최대 길이 50자로 제한
        if len(name) > 50:
            name = name[:50]

        # 여전히 유효하지 않으면 기본 이름 사용
        if not cls.is_valid_property_name(name):
            name = 'property_value'

        return name

    @classmethod
    def sanitize_properties(cls, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        속성 딕셔너리의 모든 키를 정제

        Args:
            properties: 원본 속성 딕셔너리

        Returns:
            정제된 속성 딕셔너리
        """
        sanitized = {}
        seen_names: Set[str] = set()

        for key, value in properties.items():
            # 속성명 정제
            new_key = cls.sanitize_property_name(key)

            # 중복 방지 (같은 이름으로 정제될 경우)
            if new_key in seen_names:
                counter = 2
                original_key = new_key
                while new_key in seen_names:
                    # 최대 길이를 고려하여 번호 추가
                    suffix = f'_{counter}'
                    max_base_len = 50 - len(suffix)
                    new_key = original_key[:max_base_len] + suffix
                    counter += 1

            seen_names.add(new_key)
            sanitized[new_key] = value

        return sanitized

    @classmethod
    def validate_event(cls, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        이벤트 전체를 검증하고 정제

        Args:
            event: 원본 이벤트

        Returns:
            정제된 이벤트
        """
        # 최상위 레벨 속성 정제
        sanitized_event = {}

        for key, value in event.items():
            # 미리 설정된 속성 또는 properties는 특별 처리
            if key == 'properties' and isinstance(value, dict):
                # properties 내부의 속성명 정제
                sanitized_event[key] = cls.sanitize_properties(value)
            elif key.startswith('#') or key in ['properties']:
                # 최상위 ThinkingEngine 속성은 그대로 유지
                sanitized_event[key] = value
            else:
                # 기타 최상위 속성도 정제
                new_key = cls.sanitize_property_name(key)
                sanitized_event[new_key] = value

        return sanitized_event


def validate_property_name(name: str) -> bool:
    """속성명 유효성 검증 (간편 함수)"""
    return PropertyNameValidator.is_valid_property_name(name)


def sanitize_property_name(name: str) -> str:
    """속성명 정제 (간편 함수)"""
    return PropertyNameValidator.sanitize_property_name(name)


def sanitize_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """속성 딕셔너리 정제 (간편 함수)"""
    return PropertyNameValidator.sanitize_properties(properties)


def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """이벤트 검증 및 정제 (간편 함수)"""
    return PropertyNameValidator.validate_event(event)
