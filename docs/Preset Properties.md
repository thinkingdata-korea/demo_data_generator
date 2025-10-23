### 1. 일반 속성 및 시스템 필드 개요

| 구분            | 규칙/특징                                       | 사용 목적                                                             | 비고                                                               |
| :-------------- | :---------------------------------------------- | :-------------------------------------------------------------------- | :----------------------------------------------------------------- |
| **프리셋 속성** | `#`로 시작하며, **이벤트 속성**으로만 사용됨.   | 유저 행동 이벤트에 대한 보편적인 환경 정보 제공.                      | `#ip`를 제외하고 직접 사용은 권장되지 않음.                        |
| **시스템 필드** | `#account_id`, `#event_time` 등 특수 목적 필드. | 데이터 구조 및 데이터베이스 관리용. 분석 모델에서 직접 사용되지 않음. | **이벤트/유저 속성으로 사용할 수 없음.** 데이터 전송 시 포함 금지. |

---

### 2. 플랫폼 독립적/서버 수집 프리셋 속성 (공통 속성)

이 속성들은 대부분의 플랫폼에서 수집되거나, 서버 측에서 **`#ip`**를 기반으로 생성됩니다.

| 속성 이름            | 이름           | 유형   | 수집 주체 및 타이밍 | 설명                                                                                   |
| :------------------- | :------------- | :----- | :------------------ | :------------------------------------------------------------------------------------- |
| **#ip**              | IP 주소        | String | 서버/직접 설정      | 유저의 IP 주소. TE는 이를 사용해 지리적 위치를 식별함. **(서버 SDK는 직접 설정 필요)** |
| **#country**         | 국가/지역      | String | 서버 측에서 수집    | IP 주소를 기반으로 결정됨.                                                             |
| **#country_code**    | 국가/지역 코드 | String | 서버 측에서 수집    | ISO 3166-1 alpha-2 형식 코드 (예: KR, US).                                             |
| **#province**        | 도/주          | String | 서버 측에서 수집    | IP 주소를 기반으로 결정됨.                                                             |
| **#city**            | 도시           | String | 서버 측에서 수집    | IP 주소를 기반으로 결정됨.                                                             |
| **#lib**             | SDK 유형       | String | 초기화 시 1회 수집  | 사용 중인 SDK의 종류 (Android, iOS, Java, JavaScript 등).                              |
| **#lib_version**     | SDK 버전       | String | 초기화 시 1회 수집  | 현재 사용 중인 SDK의 버전.                                                             |
| **#zone_offset**     | 시간대 오프셋  | Number | 이벤트 발생 시 수집 | 디바이스의 시간대 (UTC와의 오프셋 값).                                                 |
| **#device_id**       | 디바이스 ID    | String | 초기화 시 1회 수집  | 디바이스의 고유 식별자 (IDFV/UUID, AndroidID 등).                                      |
| **#screen_height**   | 화면 높이      | Number | 초기화 시 1회 수집  | 디바이스 화면의 픽셀 높이.                                                             |
| **#screen_width**    | 화면 너비      | Number | 초기화 시 1회 수집  | 디바이스 화면의 픽셀 너비.                                                             |
| **#system_language** | 시스템 언어    | String | 초기화 시 1회 수집  | 디바이스의 시스템 언어 (ISO 639-1 형식).                                               |

---

### 3. 클라이언트/브라우저 환경 종속 프리셋 속성

이 속성들은 Android, iOS, Web(JS)와 같이 **클라이언트 환경**에서만 수집되는 정보입니다.

| 속성 이름            | 이름               | 유형   | 수집 타이밍         | 플랫폼     | 설명                                          |
| :------------------- | :----------------- | :----- | :------------------ | :--------- | :-------------------------------------------- |
| **#os**              | 운영체제(OS)       | String | 초기화 시 1회 수집  | All Client | OS 종류 (Android, iOS 등).                    |
| **#os_version**      | OS 버전            | String | 초기화 시 1회 수집  | All Client | 디바이스의 운영 체제 버전.                    |
| **#manufacturer**    | 제조사             | String | 초기화 시 1회 수집  | Mobile     | 디바이스를 제조한 회사 (Apple, Samsung 등).   |
| **#device_model**    | 디바이스 모델      | String | 초기화 시 1회 수집  | All Client | 디바이스 모델명 (iPhone 13, Galaxy S21 등).   |
| **#device_type**     | 디바이스 타입      | String | 초기화 시 1회 수집  | All Client | 디바이스 유형 ("Phone", "Tablet" 등).         |
| **#app_version**     | 앱 버전            | String | 초기화 시 1회 수집  | Mobile     | 현재 설치된 앱의 버전.                        |
| **#bundle_id**       | 앱 고유 식별자     | String | 초기화 시 1회 수집  | Mobile     | 앱의 고유 패키지 이름 또는 프로세스 이름.     |
| **#network_type**    | 네트워크 상태      | String | 초기화/변경 시 수집 | Mobile     | 데이터 전송 시 네트워크 상태 (WIFI, 4G 등).   |
| **#carrier**         | 통신사             | String | 초기화 시 1회 수집  | Mobile     | 디바이스가 연결된 통신사.                     |
| **#install_time**    | 앱 설치 시간       | Time   | 초기화 시 1회 수집  | Mobile     | 앱이 디바이스에 설치된 시간.                  |
| **#simulator**       | 시뮬레이터         | Number | 초기화 시 1회 수집  | Mobile     | 실제 디바이스 여부 (**true/false**).          |
| **#ram**             | RAM 상태           | String | 이벤트 발생 시 수집 | Mobile     | 사용 가능한 RAM / 총 RAM.                     |
| **#disk**            | 스토리지 상태      | String | 이벤트 발생 시 수집 | Mobile     | 사용 가능한 스토리지 / 총 스토리지.           |
| **#fps**             | 프레임레이트       | Number | 이벤트 발생 시 수집 | Mobile     | 현재 디바이스 화면의 초당 프레임 수.          |
| **#browser**         | 브라우저 종류      | String | 초기화 시 1회 수집  | Web        | 사용 중인 브라우저 종류 (Chrome, Firefox 등). |
| **#browser_version** | 브라우저 버전      | String | 초기화 시 1회 수집  | Web        | 사용 중인 브라우저 버전.                      |
| **#ua**              | 유저 에이전트 정보 | String | 초기화 시 1회 수집  | Web        | OS, CPU, 브라우저 등 상세 정보.               |
| **#utm**             | 광고 캠페인 출처   | String | 초기화 시 1회 수집  | Web        | 유저 유입 광고/캠페인 정보.                   |

---

### 4. 자동 수집 이벤트 전용 프리셋 속성

이 속성들은 특정 자동 수집 이벤트 발생 시에만 포함되어 추가적인 문맥 정보를 제공합니다.

| 속성 이름                   | 이벤트 유형                   | 유형          | 설명                                                                             | 플랫폼     |
| :-------------------------- | :---------------------------- | :------------ | :------------------------------------------------------------------------------- | :--------- |
| **#resume_from_background** | `ta_app_start`                | String        | 백그라운드에서 재시작되었는지 여부.                                              | Mobile     |
| **#start_reason**           | `ta_app_start`                | String (JSON) | URL 또는 Intent로 앱이 실행된 경우의 시작 원인.                                  | Mobile     |
| **#background_duration**    | `ta_app_start`, `기타`        | Number        | 백그라운드에 머문 시간 (초 단위).                                                | Mobile     |
| **#duration**               | `ta_app_end`, `기타`          | Number        | 앱 종료 또는 이벤트 시작부터 경과 시간 (초 단위).                                | All Client |
| **#title**                  | `ta_app_view`, `ta_app_click` | String        | 페이지/Activity/View Controller의 제목.                                          | All Client |
| **#screen_name**            | `ta_app_view`, `ta_app_click` | String        | 페이지/Activity/View Controller의 클래스명 또는 카테고리명.                      | Mobile     |
| **#url**                    | `ta_app_view`                 | String        | 현재 페이지의 URL. **(Web: `location.href`, Mobile: `getScreenUrl()` 설정)**     | All Client |
| **#url_path**               | `ta_app_view`                 | String        | 현재 페이지의 경로. **(Web: `location.pathname`)**                               | Web        |
| **#referrer**               | `ta_app_view`                 | String        | 이전 페이지의 URL. **(Web: `document.referrer`, Mobile: `getScreenUrl()` 설정)** | All Client |
| **#referrer_host**          | `ta_app_view`                 | String        | 이전 페이지의 도메인.                                                            | Web        |
| **#element_id**             | `ta_app_click`                | String        | 클릭된 View의 ID.                                                                | Mobile     |
| **#element_type**           | `ta_app_click`                | String        | 클릭된 View의 타입 (Button, TextView 등).                                        | Mobile     |
| **#element_selector**       | `ta_app_click`                | String        | 클릭된 View의 `viewPath` 기반 선택자.                                            | Mobile     |
| **#element_position**       | `ta_app_click`                | String        | 클릭된 View의 위치 정보.                                                         | Mobile     |
| **#element_content**        | `ta_app_click`                | String        | 클릭된 View 위에 표시된 내용.                                                    | Mobile     |
| **#app_crashed_reason**     | `ta_app_crash`                | String        | 크래시 발생 시의 스택 트레이스 정보.                                             | iOS        |

---

### 5. 시스템 필드 상세 목록

이 필드들은 데이터베이스 관리 및 데이터 구조에 사용되며, 분석 모델에서는 제한적으로 사용됩니다.

#### 5.1. 이벤트 테이블 시스템 필드

| 필드 이름           | 이름                        | 유형   | 설명                                         |
| :------------------ | :-------------------------- | :----- | :------------------------------------------- |
| **$part_event**     | 이벤트 분할 필드            | 텍스트 | `#event_name` (이벤트 이름)에서 가져옴.      |
| **$part_date**      | 날짜 분할 필드              | 시간   | `#event_time` (이벤트 발생 날짜)에서 가져옴. |
| **#app_id**         | 프로젝트 ID                 | 텍스트 | 이벤트가 속한 프로젝트의 ID.                 |
| **#user_id**        | 유저 고유 ID                | 숫자   | 시스템에서 유저를 식별하는 고유 ID.          |
| **#account_id**     | 계정 ID                     | 텍스트 | 로그인 상태의 유저 식별자.                   |
| **#distinct_id**    | 게스트 ID                   | 텍스트 | 비로그인 상태의 유저 식별자.                 |
| **#event_name**     | 이벤트 이름                 | 텍스트 | 이벤트의 이름.                               |
| **#event_time**     | 이벤트 시간                 | 시간   | 이벤트 발생 시간.                            |
| **#server_time**    | 서버 시간                   | 시간   | 서버가 데이터를 수신한 시간.                 |
| **#dw_create_time** | 최초 데이터베이스 입력 시간 | 시간   | 해당 이벤트 데이터가 처음 DB에 입력된 시간.  |
| **#dw_update_time** | 데이터베이스 업데이트 시간  | 시간   | 해당 이벤트 데이터가 DB에서 업데이트된 시간. |
| **#kafka_offset**   | Kafka 오프셋 값             | 숫자   | 이벤트가 Kafka에 저장된 위치.                |
| **#uuid**           | UUID                        | 텍스트 | 이벤트의 고유 식별 ID.                       |

#### 5.2. 유저 테이블 시스템 필드

| 필드 이름           | 이름                       | 유형   | 설명                                                      |
| :------------------ | :------------------------- | :----- | :-------------------------------------------------------- |
| **#user_id**        | 유저 고유 ID               | 숫자   | 시스템에서 유저를 식별하는 고유 ID.                       |
| **#account_id**     | 계정 ID                    | 텍스트 | 유저의 로그인 계정 식별자.                                |
| **#distinct_id**    | 게스트 ID                  | 텍스트 | 비로그인 상태의 유저 식별자.                              |
| **#active_time**    | 활성화 시간                | 시간   | 유저의 첫 데이터 (`#time`) 기록 시간.                     |
| **#reg_time**       | 등록 시간                  | 시간   | 유저의 첫 계정 ID 포함 데이터 (`#time`) 기록 시간.        |
| **#update_time**    | 업데이트 시간              | 시간   | 유저 속성 데이터 중 가장 최근에 수신된 데이터 시간.       |
| **#server_time**    | 서버 시간                  | 시간   | 유저 속성 데이터 중 가장 최근에 서버에서 처리된 시간.     |
| **#dw_update_time** | 데이터베이스 업데이트 시간 | 시간   | 해당 유저 데이터가 가장 최근에 갱신된 시간.               |
| **#event_date**     | 최신 이벤트 날짜           | 숫자   | 유저의 가장 최신 이벤트가 DB에 입력된 날짜.               |
| **#user_operation** | 유저 작업 유형             | 텍스트 | 유저 속성 데이터가 수행한 작업 유형 (예: 추가, 업데이트). |
| **#kafka_offset**   | Kafka 오프셋 값            | 숫자   | 유저 속성 데이터가 Kafka에 저장된 위치.                   |
| **#uuid**           | UUID                       | 텍스트 | 유저 속성 데이터를 고유하게 식별하는 ID.                  |
