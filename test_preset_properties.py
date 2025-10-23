"""
프리셋 속성 통합 테스트
"""
import json
from datetime import datetime, date
from data_generator.config.config_schema import DataGeneratorConfig, IndustryType, PlatformType
from data_generator.generators.preset_properties import PresetPropertiesGenerator
from data_generator.models.user import User, UserSegment


def test_preset_properties_mobile():
    """모바일 앱 프리셋 속성 테스트"""
    print("=== Testing Mobile App Preset Properties ===")

    gen = PresetPropertiesGenerator(PlatformType.MOBILE_APP, "Test Game")
    props = gen.generate("user_001", datetime.now())

    # 공통 속성 확인
    assert "#ip" in props
    assert "#country" in props
    assert "#device_id" in props
    assert "#screen_width" in props
    assert "#system_language" in props

    # 모바일 전용 속성 확인
    assert "#os" in props
    assert "#os_version" in props
    assert "#manufacturer" in props
    assert "#device_model" in props
    assert "#app_version" in props
    assert "#bundle_id" in props
    assert "#network_type" in props

    print(f"✓ Found {len(props)} preset properties")
    for key in sorted(props.keys()):
        print(f"  {key}: {props[key]}")


def test_preset_properties_web():
    """웹 프리셋 속성 테스트"""
    print("\n=== Testing Web Preset Properties ===")

    gen = PresetPropertiesGenerator(PlatformType.WEB, "Test Web App")
    props = gen.generate("user_002", None)

    # 공통 속성 확인
    assert "#ip" in props
    assert "#country" in props
    assert "#device_id" in props

    # 웹 전용 속성 확인
    assert "#browser" in props
    assert "#browser_version" in props
    assert "#ua" in props
    assert "#os" in props

    print(f"✓ Found {len(props)} preset properties")
    for key in sorted(props.keys()):
        print(f"  {key}: {props[key]}")


def test_preset_properties_consistency():
    """동일 유저에 대한 프리셋 속성 일관성 테스트"""
    print("\n=== Testing Preset Properties Consistency ===")

    gen = PresetPropertiesGenerator(PlatformType.MOBILE_APP, "Test Game")

    # 동일한 user_id로 여러 번 생성
    props1 = gen.generate("user_001", datetime.now())
    props2 = gen.generate("user_001", datetime.now())

    # device_id는 user_id 기반이므로 동일해야 함
    assert props1["#device_id"] == props2["#device_id"]
    print(f"✓ Device ID consistency verified: {props1['#device_id']}")


def test_preset_properties_platform_differences():
    """플랫폼별 프리셋 속성 차이 테스트"""
    print("\n=== Testing Platform-Specific Differences ===")

    mobile_gen = PresetPropertiesGenerator(PlatformType.MOBILE_APP, "Test")
    web_gen = PresetPropertiesGenerator(PlatformType.WEB, "Test")
    desktop_gen = PresetPropertiesGenerator(PlatformType.DESKTOP, "Test")

    mobile_props = mobile_gen.generate("user", datetime.now())
    web_props = web_gen.generate("user", None)
    desktop_props = desktop_gen.generate("user", None)

    # 모바일에만 있는 속성
    assert "#app_version" in mobile_props
    assert "#app_version" not in web_props
    assert "#app_version" not in desktop_props

    # 웹에만 있는 속성
    assert "#browser" in web_props
    assert "#browser" not in mobile_props
    assert "#browser" not in desktop_props

    print("✓ Mobile-only properties:", [k for k in mobile_props.keys() if k not in web_props])
    print("✓ Web-only properties:", [k for k in web_props.keys() if k not in mobile_props])
    print("✓ Desktop properties:", list(desktop_props.keys()))


if __name__ == "__main__":
    try:
        test_preset_properties_mobile()
        test_preset_properties_web()
        test_preset_properties_consistency()
        test_preset_properties_platform_differences()

        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise
