"""
속성명 검증 테스트
"""
from data_generator.utils.property_validator import PropertyNameValidator

# 테스트 케이스
test_cases = [
    # (원본 속성명, 기대되는 결과)
    ("valid_property", "valid_property"),  # 정상
    ("property.with.dots", "property_with_dots"),  # 점을 밑줄로 변환
    ("property-with-hyphens", "property_with_hyphens"),  # 하이픈을 밑줄로 변환
    ("property with spaces", "property_with_spaces"),  # 공백을 밑줄로 변환
    ("123numeric_start", "_123numeric_start"),  # 숫자로 시작하면 앞에 밑줄 추가
    ("special!@#chars", "specialchars"),  # 특수문자 제거
    ("#type", "#type"),  # 미리 설정된 속성은 그대로
    ("#event_name", "#event_name"),  # 미리 설정된 속성은 그대로
    ("#custom_prop", "custom_prop"),  # 미리 설정되지 않은 # 속성은 # 제거
    ("unlocked_features_or_content_info.content_type", "unlocked_features_or_content_info_content_type"),
    ("rewards_granted_info.reward_type", "rewards_granted_info_reward_type"),
    ("player_party_info.unit_id", "player_party_info_unit_id"),
]

print("=" * 80)
print("속성명 검증 테스트")
print("=" * 80)

all_passed = True

for original, expected in test_cases:
    sanitized = PropertyNameValidator.sanitize_property_name(original)
    is_valid = PropertyNameValidator.is_valid_property_name(sanitized)
    passed = (sanitized == expected) and is_valid

    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"\n{status}")
    print(f"  원본:    {original}")
    print(f"  기대값:  {expected}")
    print(f"  결과:    {sanitized}")
    print(f"  유효성:  {is_valid}")

    if not passed:
        all_passed = False

print("\n" + "=" * 80)

# 딕셔너리 테스트
print("\n딕셔너리 속성명 정제 테스트")
print("=" * 80)

test_dict = {
    "valid_property": "value1",
    "property.with.dots": "value2",
    "property-with-hyphens": "value3",
    "unlocked_features_or_content_info.content_type": "value4",
    "rewards_granted_info.reward_type": "value5",
    "#event_name": "test_event",
    "123numeric": "value6",
}

print("\n원본 딕셔너리:")
for key, value in test_dict.items():
    print(f"  {key}: {value}")

sanitized_dict = PropertyNameValidator.sanitize_properties(test_dict)

print("\n정제된 딕셔너리:")
for key, value in sanitized_dict.items():
    is_valid = PropertyNameValidator.is_valid_property_name(key)
    status = "✓" if is_valid else "✗"
    print(f"  {status} {key}: {value}")

print("\n" + "=" * 80)
if all_passed:
    print("✓ 모든 테스트 통과!")
else:
    print("✗ 일부 테스트 실패")
print("=" * 80)
