"""
프리셋 속성 생성기 - 플랫폼별 필수 프리셋 속성 자동 생성
"""
import random
from typing import Dict, Any, Optional
from datetime import datetime
from ..config.config_schema import PlatformType


class PresetPropertiesGenerator:
    """플랫폼별 프리셋 속성 생성기"""

    # 공통 프리셋 속성 (모든 플랫폼)
    COMMON_PRESET_PROPERTIES = [
        "#ip",
        "#country",
        "#country_code",
        "#province",
        "#city",
        "#lib",
        "#lib_version",
        "#zone_offset",
        "#device_id",
        "#screen_height",
        "#screen_width",
        "#system_language",
    ]

    # 모바일 전용 프리셋 속성
    MOBILE_PRESET_PROPERTIES = [
        "#os",
        "#os_version",
        "#manufacturer",
        "#device_model",
        "#device_type",
        "#app_version",
        "#bundle_id",
        "#network_type",
        "#carrier",
        "#install_time",
        "#simulator",
        "#ram",
        "#disk",
        "#fps",
    ]

    # 웹 전용 프리셋 속성
    WEB_PRESET_PROPERTIES = [
        "#os",
        "#os_version",
        "#browser",
        "#browser_version",
        "#ua",
        "#utm",
    ]

    # 데스크톱 전용 프리셋 속성
    DESKTOP_PRESET_PROPERTIES = [
        "#os",
        "#os_version",
        "#device_model",
    ]

    # 샘플 데이터
    COUNTRIES = [
        {"name": "South Korea", "code": "KR", "province": "Seoul", "city": "Gangnam"},
        {"name": "United States", "code": "US", "province": "California", "city": "San Francisco"},
        {"name": "Japan", "code": "JP", "province": "Tokyo", "city": "Shibuya"},
        {"name": "China", "code": "CN", "province": "Beijing", "city": "Chaoyang"},
    ]

    MOBILE_OS = ["Android", "iOS"]
    ANDROID_VERSIONS = ["13", "12", "11", "10"]
    IOS_VERSIONS = ["17.2", "17.1", "16.5", "16.4"]

    MANUFACTURERS = {
        "Android": ["Samsung", "LG", "Google", "Xiaomi"],
        "iOS": ["Apple"],
    }

    DEVICE_MODELS = {
        "Samsung": ["Galaxy S23", "Galaxy S22", "Galaxy A54"],
        "LG": ["V60 ThinQ", "G8 ThinQ"],
        "Google": ["Pixel 7", "Pixel 6"],
        "Xiaomi": ["Mi 13", "Redmi Note 12"],
        "Apple": ["iPhone 15 Pro", "iPhone 14", "iPhone 13"],
    }

    NETWORK_TYPES = ["WIFI", "4G", "5G", "3G"]
    CARRIERS = ["SKT", "KT", "LG U+", "Verizon", "AT&T"]

    WEB_OS = ["Windows", "macOS", "Linux"]
    WEB_OS_VERSIONS = {
        "Windows": ["11", "10"],
        "macOS": ["14.0", "13.5", "13.0"],
        "Linux": ["Ubuntu 22.04", "Ubuntu 20.04"],
    }

    BROWSERS = ["Chrome", "Safari", "Firefox", "Edge"]
    BROWSER_VERSIONS = {
        "Chrome": ["120.0", "119.0", "118.0"],
        "Safari": ["17.2", "17.1", "16.6"],
        "Firefox": ["121.0", "120.0", "119.0"],
        "Edge": ["120.0", "119.0"],
    }

    DESKTOP_OS = ["Windows", "macOS", "Linux"]
    LANGUAGES = ["ko", "en", "ja", "zh"]

    def __init__(self, platform: PlatformType, product_name: str):
        """
        Args:
            platform: 플랫폼 유형
            product_name: 제품/앱 이름
        """
        self.platform = platform
        self.product_name = product_name

    def generate(self, user_id: str, install_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        플랫폼에 맞는 프리셋 속성 생성

        Args:
            user_id: 유저 ID (디바이스 ID 생성에 사용)
            install_date: 앱 설치 시간 (모바일 전용)

        Returns:
            프리셋 속성 딕셔너리
        """
        preset_props = {}

        # 공통 속성 추가
        preset_props.update(self._generate_common_properties(user_id))

        # 플랫폼별 속성 추가
        if self.platform == PlatformType.MOBILE_APP:
            preset_props.update(self._generate_mobile_properties(install_date))
        elif self.platform == PlatformType.WEB:
            preset_props.update(self._generate_web_properties())
        elif self.platform == PlatformType.DESKTOP:
            preset_props.update(self._generate_desktop_properties())
        elif self.platform == PlatformType.HYBRID:
            # 하이브리드는 웹 + 모바일 속성 조합
            if random.random() < 0.7:  # 70% 모바일
                preset_props.update(self._generate_mobile_properties(install_date))
            else:  # 30% 웹
                preset_props.update(self._generate_web_properties())

        return preset_props

    def _generate_common_properties(self, user_id: str) -> Dict[str, Any]:
        """공통 프리셋 속성 생성"""
        country = random.choice(self.COUNTRIES)

        return {
            "#ip": self._generate_fake_ip(),
            "#country": country["name"],
            "#country_code": country["code"],
            "#province": country["province"],
            "#city": country["city"],
            "#lib": self._get_lib_name(),
            "#lib_version": self._generate_lib_version(),
            "#zone_offset": random.choice([9.0, -8.0, -5.0, 0.0]),  # KR, US West, US East, UTC
            "#device_id": self._generate_device_id(user_id),
            "#screen_height": random.choice([2400, 1920, 1440, 1080]),
            "#screen_width": random.choice([1080, 1440, 720, 1920]),
            "#system_language": random.choice(self.LANGUAGES),
        }

    def _generate_mobile_properties(self, install_date: Optional[datetime]) -> Dict[str, Any]:
        """모바일 프리셋 속성 생성"""
        os = random.choice(self.MOBILE_OS)
        manufacturer = random.choice(self.MANUFACTURERS[os])

        props = {
            "#os": os,
            "#os_version": random.choice(self.ANDROID_VERSIONS if os == "Android" else self.IOS_VERSIONS),
            "#manufacturer": manufacturer,
            "#device_model": random.choice(self.DEVICE_MODELS[manufacturer]),
            "#device_type": "Phone" if random.random() < 0.8 else "Tablet",
            "#app_version": self._generate_app_version(),
            "#bundle_id": self._generate_bundle_id(os),
            "#network_type": random.choice(self.NETWORK_TYPES),
            "#carrier": random.choice(self.CARRIERS),
            "#simulator": 0,  # 실제 디바이스
            "#ram": f"{random.randint(2000, 4000)}/{random.randint(6000, 12000)}MB",
            "#disk": f"{random.randint(5000, 20000)}/{random.randint(64000, 256000)}MB",
            "#fps": random.randint(55, 60),
        }

        if install_date:
            props["#install_time"] = install_date.strftime("%Y-%m-%d %H:%M:%S")

        return props

    def _generate_web_properties(self) -> Dict[str, Any]:
        """웹 프리셋 속성 생성"""
        os = random.choice(self.WEB_OS)
        browser = random.choice(self.BROWSERS)

        # Safari는 macOS에서만
        if browser == "Safari":
            os = "macOS"

        return {
            "#os": os,
            "#os_version": random.choice(self.WEB_OS_VERSIONS[os]),
            "#browser": browser,
            "#browser_version": random.choice(self.BROWSER_VERSIONS[browser]),
            "#ua": self._generate_user_agent(os, browser),
            "#utm": "" if random.random() < 0.7 else self._generate_utm_params(),
        }

    def _generate_desktop_properties(self) -> Dict[str, Any]:
        """데스크톱 프리셋 속성 생성"""
        os = random.choice(self.DESKTOP_OS)

        return {
            "#os": os,
            "#os_version": random.choice(self.WEB_OS_VERSIONS[os]),
            "#device_model": f"{os} Desktop",
        }

    def _get_lib_name(self) -> str:
        """SDK 이름 반환"""
        if self.platform == PlatformType.MOBILE_APP:
            return random.choice(["Android", "iOS"])
        elif self.platform == PlatformType.WEB:
            return "JavaScript"
        elif self.platform == PlatformType.DESKTOP:
            return random.choice(["Windows", "macOS", "Linux"])
        else:
            return "JavaScript"

    def _generate_lib_version(self) -> str:
        """SDK 버전 생성"""
        return f"{random.randint(2, 4)}.{random.randint(0, 9)}.{random.randint(0, 20)}"

    def _generate_device_id(self, user_id: str) -> str:
        """디바이스 ID 생성 (user_id 기반으로 일관성 있게)"""
        # user_id를 해시하여 일관된 device_id 생성
        hash_val = abs(hash(user_id))
        return f"device_{hash_val:016x}"

    def _generate_fake_ip(self) -> str:
        """가짜 IP 주소 생성"""
        return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def _generate_app_version(self) -> str:
        """앱 버전 생성"""
        return f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 20)}"

    def _generate_bundle_id(self, os: str) -> str:
        """번들 ID 생성"""
        package_name = self.product_name.lower().replace(" ", "").replace("-", "")
        if os == "Android":
            return f"com.{package_name}.app"
        else:  # iOS
            return f"com.company.{package_name}"

    def _generate_user_agent(self, os: str, browser: str) -> str:
        """User Agent 문자열 생성"""
        if os == "Windows":
            return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/120.0.0.0"
        elif os == "macOS":
            return f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/120.0.0.0"
        else:  # Linux
            return f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/120.0.0.0"

    def _generate_utm_params(self) -> str:
        """UTM 파라미터 생성"""
        campaigns = ["google_ads", "facebook_ads", "email_campaign", "organic"]
        sources = ["google", "facebook", "newsletter", "direct"]

        campaign = random.choice(campaigns)
        source = random.choice(sources)

        return f"utm_source={source}&utm_medium=cpc&utm_campaign={campaign}"
