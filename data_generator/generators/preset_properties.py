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

    # 샘플 데이터 (논리적 일관성 보장)
    # 국가별 locale, timezone, carriers 매핑
    COUNTRIES = [
        {
            "name": "South Korea",
            "code": "KR",
            "provinces": [
                {"name": "Seoul", "cities": ["Gangnam", "Gangbuk", "Mapo", "Songpa"]},
                {"name": "Busan", "cities": ["Haeundae", "Nampo", "Seomyeon"]},
                {"name": "Incheon", "cities": ["Songdo", "Bupyeong"]},
            ],
            "carriers": ["SKT", "KT", "LG U+"],
            "locale": "ko_KR",
            "zone_offset": 9.0,
            "language": "ko",
        },
        {
            "name": "United States",
            "code": "US",
            "provinces": [
                {"name": "California", "cities": ["San Francisco", "Los Angeles", "San Diego"]},
                {"name": "New York", "cities": ["New York", "Buffalo", "Rochester"]},
                {"name": "Texas", "cities": ["Austin", "Houston", "Dallas"]},
            ],
            "carriers": ["Verizon", "AT&T", "T-Mobile", "Sprint"],
            "locale": "en_US",
            "zone_offset": -8.0,  # PST
            "language": "en",
        },
        {
            "name": "Japan",
            "code": "JP",
            "provinces": [
                {"name": "Tokyo", "cities": ["Shibuya", "Shinjuku", "Akihabara"]},
                {"name": "Osaka", "cities": ["Umeda", "Namba", "Tennoji"]},
            ],
            "carriers": ["NTT Docomo", "SoftBank", "au"],
            "locale": "ja_JP",
            "zone_offset": 9.0,
            "language": "ja",
        },
        {
            "name": "China",
            "code": "CN",
            "provinces": [
                {"name": "Beijing", "cities": ["Chaoyang", "Haidian"]},
                {"name": "Shanghai", "cities": ["Pudong", "Huangpu"]},
            ],
            "carriers": ["China Mobile", "China Unicom", "China Telecom"],
            "locale": "zh_CN",
            "zone_offset": 8.0,
            "language": "zh",
        },
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

    def __init__(
        self,
        platform: PlatformType,
        product_name: str,
        intelligent_generator=None  # Optional[IntelligentPropertyGenerator]
    ):
        """
        Args:
            platform: 플랫폼 유형
            product_name: 제품/앱 이름
            intelligent_generator: AI 기반 속성 생성기 (선택)
        """
        self.platform = platform
        self.product_name = product_name
        self.intelligent_generator = intelligent_generator

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

        # 플랫폼별 속성 추가 (국가 정보 전달)
        country_info = preset_props.pop("_country_info", None)

        if self.platform == PlatformType.MOBILE_APP:
            preset_props.update(self._generate_mobile_properties(install_date, country_info))
        elif self.platform == PlatformType.WEB:
            preset_props.update(self._generate_web_properties())
        elif self.platform == PlatformType.DESKTOP:
            preset_props.update(self._generate_desktop_properties())
        elif self.platform == PlatformType.HYBRID:
            # 하이브리드는 웹 + 모바일 속성 조합
            if random.random() < 0.7:  # 70% 모바일
                preset_props.update(self._generate_mobile_properties(install_date, country_info))
            else:  # 30% 웹
                preset_props.update(self._generate_web_properties())

        return preset_props

    def _generate_common_properties(self, user_id: str) -> Dict[str, Any]:
        """공통 프리셋 속성 생성 (논리적 일관성 보장)"""
        # 국가 선택 (이후 province, city, carrier가 이에 맞춰 선택됨)
        country = random.choice(self.COUNTRIES)
        province = random.choice(country["provinces"])
        city = random.choice(province["cities"])

        return {
            "#ip": self._generate_fake_ip(),
            "#country": country["name"],
            "#country_code": country["code"],
            "#province": province["name"],
            "#city": city,
            "#lib": self._get_lib_name(),
            "#lib_version": self._generate_lib_version(),
            "#zone_offset": country["zone_offset"],
            "#device_id": self._generate_device_id(user_id),
            "#screen_height": random.choice([2400, 1920, 1440, 1080]),
            "#screen_width": random.choice([1080, 1440, 720, 1920]),
            "#system_language": country["language"],
            "_country_info": country,  # 임시 저장 (carrier, name locale 생성에 사용)
        }

    def _generate_mobile_properties(self, install_date: Optional[datetime], country_info: Optional[Dict] = None) -> Dict[str, Any]:
        """모바일 프리셋 속성 생성 (논리적 일관성 보장)"""
        os = random.choice(self.MOBILE_OS)
        manufacturer = random.choice(self.MANUFACTURERS[os])

        # 국가에 맞는 carrier 선택
        if country_info and "carriers" in country_info:
            carrier = random.choice(country_info["carriers"])
        else:
            # fallback: 임의 carrier (논리적 일관성은 보장되지 않음)
            carrier = random.choice(["SKT", "Verizon"])

        props = {
            "#os": os,
            "#os_version": random.choice(self.ANDROID_VERSIONS if os == "Android" else self.IOS_VERSIONS),
            "#manufacturer": manufacturer,
            "#device_model": random.choice(self.DEVICE_MODELS[manufacturer]),
            "#device_type": "Phone" if random.random() < 0.8 else "Tablet",
            "#app_version": self._generate_app_version(),
            "#bundle_id": self._generate_bundle_id(os),
            "#network_type": random.choice(self.NETWORK_TYPES),
            "#carrier": carrier,  # 국가에 맞는 carrier
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

    def generate_event_specific_properties(
        self,
        event_name: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        이벤트별 전용 속성 생성

        Args:
            event_name: 이벤트 이름
            session_context: 세션 컨텍스트 (session_start, background_duration 등)

        Returns:
            이벤트별 전용 속성 딕셔너리
        """
        props = {}

        # app_start 이벤트 속성 (ta_app_start, te_app_start 등)
        if "app_start" in event_name.lower():
            props.update(self._generate_app_start_properties(session_context))

        # app_end 이벤트 속성 (ta_app_end, te_app_end 등)
        elif "app_end" in event_name.lower():
            props.update(self._generate_app_end_properties(session_context))

        # app_view 이벤트 속성 (ta_app_view, te_app_view 등)
        elif "app_view" in event_name.lower():
            props.update(self._generate_page_view_properties())

        # app_click 이벤트 속성 (ta_app_click, te_app_click 등)
        elif "app_click" in event_name.lower():
            props.update(self._generate_click_properties())

        # app_crash 이벤트 속성 (ta_app_crash, te_app_crash 등)
        elif "app_crash" in event_name.lower():
            props.update(self._generate_crash_properties())

        return props

    def _generate_app_start_properties(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """ta_app_start / te_app_start 이벤트 전용 속성"""
        props = {}

        # 백그라운드에서 재시작 여부
        is_resume = context.get("is_resume", False) if context else random.random() < 0.3
        props["#resume_from_background"] = is_resume

        # 백그라운드 지속 시간 (재시작인 경우에만)
        if is_resume:
            bg_duration = context.get("background_duration", random.randint(10, 300)) if context else random.randint(10, 300)
            props["#background_duration"] = bg_duration

        # 시작 원인 (URL/Intent로 실행된 경우)
        if random.random() < 0.2:  # 20% 확률로 딥링크 시작
            start_reasons = [
                '{"url": "app://home"}',
                '{"url": "app://product/123"}',
                '{"url": "app://promotion"}',
                '{"intent": "android.intent.action.VIEW"}',
            ]
            props["#start_reason"] = random.choice(start_reasons)

        return props

    def _generate_app_end_properties(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """ta_app_end / te_app_end 이벤트 전용 속성"""
        props = {}

        # 앱 사용 시간 (초 단위)
        if context and "session_duration" in context:
            duration = context["session_duration"]
        else:
            # 일반적인 세션 시간: 30초 ~ 30분
            duration = random.randint(30, 1800)

        props["#duration"] = duration

        return props

    def _generate_page_view_properties(self) -> Dict[str, Any]:
        """
        ta_app_view / te_app_view 이벤트 전용 속성
        AI 기반 생성으로 산업별 맞춤형 값 제공
        """
        props = {}

        # AI 생성기가 있으면 맥락에 맞는 값 생성
        if self.intelligent_generator:
            # 페이지 타이틀 (AI가 산업에 맞게 생성)
            title = self.intelligent_generator.generate_property_value(
                prop_name="page_title",
                prop_type="string",
                user=None,
                event_name="app_view",
                additional_context={"type": "screen_title"}
            )
            props["#title"] = title if title else f"Screen_{random.randint(1, 10)}"

            if self.platform == PlatformType.MOBILE_APP:
                # screen_name (AI가 산업에 맞는 화면명 생성)
                screen_name = self.intelligent_generator.generate_property_value(
                    prop_name="screen_name",
                    prop_type="string",
                    user=None,
                    event_name="app_view",
                    additional_context={"type": "activity_class_name"}
                )
                props["#screen_name"] = screen_name if screen_name else f"Screen{random.randint(1, 10)}Activity"

            # URL (범용 템플릿)
            url_paths = ["home", "detail", "list", "profile", "settings", "search"]
            path = random.choice(url_paths)
            props["#url"] = f"https://example.com/{path}"
        else:
            # 폴백: 범용 템플릿 (산업 무관)
            props["#title"] = f"Screen_{random.randint(1, 10)}"

            if self.platform == PlatformType.MOBILE_APP:
                props["#screen_name"] = f"Screen{random.randint(1, 10)}Activity"

            # 범용 URL
            props["#url"] = f"https://example.com/screen_{random.randint(1, 10)}"

        # 웹 전용: url_path
        if self.platform == PlatformType.WEB:
            props["#url_path"] = props["#url"].replace("https://example.com", "")

        # Referrer (범용 - 이전 URL)
        if random.random() < 0.8:
            props["#referrer"] = f"https://example.com/screen_{random.randint(1, 10)}"
            if self.platform == PlatformType.WEB:
                props["#referrer_host"] = "example.com"
        else:
            props["#referrer"] = ""

        return props

    def _generate_click_properties(self) -> Dict[str, Any]:
        """
        ta_app_click / te_app_click 이벤트 전용 속성
        AI 기반 생성으로 산업별 맞춤형 값 제공
        """
        props = {}

        # AI 생성기가 있으면 맥락에 맞는 값 생성
        if self.intelligent_generator:
            # 페이지 타이틀
            title = self.intelligent_generator.generate_property_value(
                prop_name="page_title",
                prop_type="string",
                user=None,
                event_name="app_click",
                additional_context={"type": "screen_title"}
            )
            props["#title"] = title if title else f"Screen_{random.randint(1, 10)}"

            if self.platform == PlatformType.MOBILE_APP:
                # screen_name
                screen_name = self.intelligent_generator.generate_property_value(
                    prop_name="screen_name",
                    prop_type="string",
                    user=None,
                    event_name="app_click",
                    additional_context={"type": "activity_class_name"}
                )
                props["#screen_name"] = screen_name if screen_name else f"Screen{random.randint(1, 10)}Activity"

                # element_content (버튼 텍스트 - AI가 산업에 맞게)
                content = self.intelligent_generator.generate_property_value(
                    prop_name="button_text",
                    prop_type="string",
                    user=None,
                    event_name="app_click",
                    additional_context={"type": "button_label"}
                )
                props["#element_content"] = content if content else f"Button_{random.randint(1, 10)}"

                # 나머지는 범용 템플릿 (산업 무관)
                props["#element_id"] = f"btn_{random.randint(1, 100)}"
                props["#element_type"] = random.choice(["Button", "TextView", "ImageView", "LinearLayout"])
                props["#element_selector"] = f"Screen/Layout/Button"
                props["#element_position"] = f"{random.randint(0, 500)},{random.randint(0, 1000)}"
        else:
            # 폴백: 범용 템플릿
            props["#title"] = f"Screen_{random.randint(1, 10)}"

            if self.platform == PlatformType.MOBILE_APP:
                props["#screen_name"] = f"Screen{random.randint(1, 10)}Activity"
                props["#element_id"] = f"btn_{random.randint(1, 100)}"
                props["#element_type"] = "Button"
                props["#element_selector"] = "Screen/Layout/Button"
                props["#element_position"] = f"{random.randint(0, 500)},{random.randint(0, 1000)}"
                props["#element_content"] = f"Button_{random.randint(1, 10)}"

        return props

    def _generate_crash_properties(self) -> Dict[str, Any]:
        """ta_app_crash / te_app_crash 이벤트 전용 속성"""
        props = {}

        # 모바일만 crash reason 포함
        if self.platform == PlatformType.MOBILE_APP:
            crash_reasons = [
                "java.lang.NullPointerException: Attempt to invoke virtual method on null object",
                "java.lang.OutOfMemoryError: Failed to allocate memory",
                "android.content.ActivityNotFoundException: No Activity found to handle Intent",
                "Fatal Exception: NSInvalidArgumentException: unrecognized selector sent to instance",
                "Fatal Exception: EXC_BAD_ACCESS: Attempted to dereference null pointer",
            ]
            props["#app_crashed_reason"] = random.choice(crash_reasons)

        return props
