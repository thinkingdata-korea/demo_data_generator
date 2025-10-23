## 우리 솔루션(Thinking Engine) 데이터 구조 및 규칙 설명서

### 1. 핵심 개념: JSON 입력과 2개의 테이블

우리 솔루션의 모든 데이터는 **단일 라인 JSON** 형식으로 수신됩니다. 시스템은 이 JSON의 **`#type`** 필드 값을 확인하여, 데이터를 **'유저 테이블'** 또는 **'이벤트 테이블'**이라는 2개의 서로 다른 테이블로 라우팅하여 저장 및 갱신합니다.

- **JSON 구조:**
  - **메타데이터 (Header):** `#`으로 시작하는 필드 (예: `#type`, `#account_id`, `#time`). 데이터의 기본 정보를 담습니다.
  - **속성 (Body):** `properties`라는 객체 내부에 실제 분석할 데이터를 Key-Value 형태로 담습니다.

### 2. 데이터 라우팅 규칙: `#type`

`#type` 필드는 데이터가 어떤 테이블로 가야 할지 결정하는 '라우터'입니다.

1.  **`#type: "track"` (행동 기록)**

    - **목적:** 유저의 '행동'을 로그로 기록합니다.
    - **대상:** **'이벤트 테이블'**에 한 줄(Row)로 저장됩니다.
    - **특징:** `#event_name` 필드가 반드시 필요합니다. `properties` 안의 모든 내용은 이 이벤트의 속성이 됩니다.

2.  **`#type: "user_..."` (상태 갱신)**
    - **목적:** 유저의 '상태'를 갱신하는 '명령'입니다.
    - **대상:** **'유저 테이블'**에서 특정 유저의 데이터를 찾아 갱신합니다.
    - **특징:** `properties` 안의 내용은 갱신할 속성 값이 됩니다.

### 3. 유저 식별 로직 (The "Who")

데이터를 특정 유저에게 매핑하기 위해 3가지 ID를 사용하며, 이 관계가 가장 중요합니다.

- **`#user_id` (TE 유저 ID):** 시스템 내부에서 사용하는 유일한 유저 식별자 (Primary Key).
- **`#account_id` (계정 ID):** 로그인 시 사용하는 유저의 고유 ID.
- **`#distinct_id` (게스트 ID):** 비로그인 시 사용하는 기기 ID.

**핵심 매핑 규칙:**

1.  **`#account_id` 우선:** `#account_id`가 존재하면 항상 이 ID를 기준으로 `#user_id`를 찾습니다.
2.  **1:1 매핑:** `#user_id`와 `#account_id`는 1:1로 매핑됩니다.
3.  **1:N 매핑:** 하나의 `#account_id`는 여러 개의 `#distinct_id`를 가질 수 있습니다. (여러 기기에서 로그인)
4.  **1:1 귀속:** 하나의 `#distinct_id`는 **단 하나의 `#account_id`에만** 귀속될 수 있습니다. (게스트 ID가 한번 로그인하면 그 계정의 소유가 됨)

### 4. 테이블 1: 유저 테이블 (User "State")

유저의 현재 상태 값을 저장하는 마스터 테이블입니다.

#### 4.1. 유저 테이블 업데이트 방식 (`#type`)

이 테이블은 `#type`이 `user_...`인 JSON 명령으로만 데이터가 변경됩니다.

- **`user_set`:** 속성 값을 덮어씁니다. (예: `current_player_level`, `nick_name`)
- **`user_set_once`:** 속성 값이 존재하지 않을 때(null) 한 번만 설정합니다. (예: `first_seen_time`, `acquisition_channel`)
- **`user_add`:** 숫자형 속성 값을 더하거나 뺍니다. (예: `total_iap_amount`, `total_playtime_minutes`)
- **`user_append`:** List(배열) 속성에 요소를 추가합니다. (예: `recent_login_timestamps`)
- **`user_unset`:** 특정 속성의 값을 비웁니다 (null로 만듦).
- **`user_del`:** 유저 데이터를 테이블에서 삭제합니다.

#### 4.2. 유저 테이블의 주요 속성 (Schema)

| 속성 이름                    | 데이터 유형         | 업데이트 방식   | 설명                                 |
| :--------------------------- | :------------------ | :-------------- | :----------------------------------- |
| `nick_name`                  | Text (string)       | `user_set`      | 유저의 현재 닉네임 (변경 가능)       |
| `current_player_level`       | Number              | `user_set`      | 현재 레벨 (덮어쓰기)                 |
| `current_gold_balance`       | Number              | `user_set`      | 현재 재화 보유량 (덮어쓰기)          |
| `highest_main_stage_cleared` | Text (string)       | `user_set`      | 최고 클리어 스테이지 (덮어쓰기)      |
| `first_seen_time`            | Time (string)       | `user_set_once` | 최초 접속 시각 (최초 1회만 기록)     |
| `acquisition_channel`        | Text (string)       | `user_set_once` | 최초 유입 채널 (최초 1회만 기록)     |
| `total_iap_amount`           | Number              | `user_add`      | 누적 결제액 (결제 시마다 누적)       |
| `total_playtime_minutes`     | Number              | `user_add`      | 누적 플레이 시간 (세션 종료 시 누적) |
| `recent_login_timestamps`    | List (string array) | `user_append`   | 최근 로그인 시각 목록 (배열에 추가)  |

---

### 5. 테이블 2: 이벤트 테이블 (User "Action")

유저가 발생시킨 모든 행동(로그)을 시간순으로 저장하는 테이블입니다.

#### 5.1. 이벤트 테이블 생성 방식

`#type: "track"` 및 `#event_name`이 지정된 JSON이 수신될 때마다 이 테이블에 1줄의 레코드가 생성됩니다.

#### 5.2. 이벤트 테이블의 주요 속성 (Schema)

이벤트 테이블의 속성(`properties`)은 크게 두 부분으로 나뉩니다.

**1. 공통 이벤트 속성 (모든 이벤트에 포함)**
모든 이벤트가 발생할 때 유저의 **'그 시점의 스냅샷(Snapshot)'** 정보입니다.

| 속성 이름              | 데이터 유형         | 설명                           |
| :--------------------- | :------------------ | :----------------------------- |
| `channel`              | Text (string)       | 현재 접속 채널                 |
| `server_id`            | Text (string)       | 현재 접속 서버                 |
| `tmp_level`            | Number              | 이벤트 발생 시점의 레벨        |
| `tmp_combat_power`     | Number              | 이벤트 발생 시점의 전투력      |
| `tmp_gold`             | Number              | 이벤트 발생 시점의 골드 보유량 |
| `tmp_gem`              | Number              | 이벤트 발생 시점의 젬 보유량   |
| `tmp_main_stage_id`    | Text (string)       | 이벤트 발생 시점의 스테이지 ID |
| `tmp_active_buff_list` | List (string array) | 이벤트 발생 시점의 버프 목록   |

**2. 이벤트 고유 속성 (특정 이벤트에만 포함)**
해당 이벤트의 고유한 정보입니다.

- `#event_name: "stage_clear"` (스테이지 클리어)
  - `stage_id`: "stage_001"
  - `clear_time`: 120.5
- `#event_name: "item_purchase"` (아이템 구매)
  - `item_id`: "sword_01"
  - `item_count`: 1
  - `currency_used`: "gold"
  - `price`: 1000

---

### 6. 핵심 데이터 유형 (Format) 및 제한

`properties` 내부에 사용되는 모든 데이터의 유형과 규칙입니다.

- **규칙:** 속성의 데이터 유형은 **최초 수신된 값의 유형으로 고정**됩니다. 이후 다른 유형의 값이 들어오면 해당 속성은 무시(null 처리)됩니다.

| TE 데이터 유형   | JSON 데이터 유형   | 예시                                       | 제한 사항                                                      |
| :--------------- | :----------------- | :----------------------------------------- | :------------------------------------------------------------- |
| **number**       | Number             | `123`, `1.23`                              | -9E15 ~ 9E15                                                   |
| **string**       | String             | `"ABC"`, `"Shanghai"`                      | 최대 2KB                                                       |
| **time**         | String             | `"2024-10-22 14:30:00.123"`                | "yyyy-MM-dd HH:mm:ss.SSS" 또는 "yyyy-MM-dd HH:mm:ss" 형식      |
| **boolean**      | Boolean            | `true`, `false`                            | -                                                              |
| **list**         | Array **(String)** | `["a", "1", "true"]`                       | **모든 요소가 문자열로 변환**되어 저장됩니다. 최대 500개 요소. |
| **object**       | Object             | `{"hero_name": "Liu Bei", "level": 22}`    | JSON 객체. 최대 100개의 하위 속성.                             |
| **object group** | Array **(Object)** | `[{"hero_name": "A"}, {"hero_name": "B"}]` | **객체(Object)의 배열**입니다. 최대 500개의 객체.              |

### 7. 가상 데이터 생성을 위한 요약

가상 데이터를 생성할 때는 다음 두 가지를 **항상 쌍으로** 고려해야 합니다.

1.  **행동 발생 (Event Table):** 유저가 `stage_clear` 이벤트를 발생시킵니다.
    - `#type: "track"`, `#event_name: "stage_clear"` JSON을 생성합니다.
    - `properties`에는 **공통 속성**(예: `tmp_level: 10`)과 **고유 속성**(예: `stage_id: "s1-10"`)을 포함합니다.
2.  **상태 변경 (User Table):** 위 이벤트의 결과로 유저의 상태가 변경됩니다. (예: 레벨업, 스테이지 갱신)
    - `#type: "user_set"` JSON을 별도로 생성합니다.
    - `properties`에는 `{"current_player_level": 11, "highest_main_stage_cleared": "s1-10"}`을 포함합니다.
    - 만약 재화를 얻었다면, `#type: "user_add"` JSON과 `properties`에 `{"current_gold_balance": 500}`을 포함시킬 수 있습니다.
