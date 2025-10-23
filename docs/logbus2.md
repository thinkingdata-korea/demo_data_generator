# LogBus2

## 1\. LogBus2 개요

LogBus2는 기존 LogBus를 기반으로 새롭게 개발된 로그 동기화 도구입니다. 기존 버전과 비교하면 메모리 사용량이 1/5로 줄어들었으며, 처리 속도는 5배 향상되었습니다.

LogBus2는 백엔드 로그 데이터를 TE 시스템으로 실시간 전송하는 데 사용됩니다. 핵심 원리는 Flume이나 Loggie와 유사하며, 서버의 로그 디렉터리를 모니터링하여 로그 파일에 새로운 데이터가 추가되면 이를 검증한 후 TE 시스템으로 즉시 전송합니다.

다음과 같은 경우 LogBus2를 사용하여 데이터를 전송하는 것을 권장합니다.

1.  서버 SDK, Kafka, SLS 등을 이용해 TE 포맷 데이터를 저장하는 유저로, LogBus2를 통해 데이터를 업로드하려는 경우
2.  데이터의 정확성과 다양한 속성이 중요한데, 클라이언트 SDK만으로는 요구 사항을 충족하기 어렵거나 클라이언트 SDK 연동이 불편한 경우
3.  직접 백엔드 데이터 전송 프로세스를 개발하고 싶지 않은 경우
4.  대량의 과거 데이터를 전송해야 하는 경우
5.  메모리 사용량과 전송 효율을 고려해야 하는 경우

**⚠️ 참고:** LogBus v1에서 LogBus v2로 마이그레이션하려면 씽킹데이터(ThinkingData) 기술 지원팀에 문의하세요.

## 2\. LogBus2 다운로드

- **최신 버전:** 2.1.1.7
- **업데이트 날짜:** 2025-01-20
- Linux-amd64 download
- Linux-arm64 download
- Windows download
- Mac Apple Silicon download
- Mac Intel download
- Docker Image

## 3\. 사용 전 준비

### 파일 유형

1.  업로드할 데이터가 저장된 디렉터리를 지정하고 LogBus2의 설정을 구성해야 합니다. LogBus2는 해당 디렉터리를 모니터링하여 새로운 파일이 생성되거나 기존 파일이 변경되는지 감지합니다. (새로운 파일 생성 및 기존 파일의 tail 모니터링)
2.  이미 업로드된 로그 파일의 이름을 변경하지 마세요. 파일명을 변경하면 LogBus2가 이를 새로운 파일로 인식하여 다시 업로드할 수 있으며, 이로 인해 데이터 중복이 발생할 수 있습니다.
3.  LogBus2 실행 디렉터리에는 현재 로그 전송 상태를 저장하는 스냅샷 파일이 포함되어 있습니다. `runtime` 디렉터리 내 파일을 임의로 수정하지 마세요.

### Kafka 연동

1.  Kafka 메시지 포맷을 확인하세요. LogBus2는 Kafka 메시지의 `value` 부분만 처리합니다.
2.  유저 ID가 파티션별로 분리되었는지 확인하여 데이터 순서가 뒤섞이는 문제를 방지하세요.
3.  Kafka Consumer Group을 자유롭게 사용할 수 있도록 설정하세요. 여러 개의 LogBus2 인스턴스를 운영할 경우, 이 설정이 없으면 소비 장애가 발생할 수 있습니다.
4.  기본적으로 `earliest` 오프셋부터 메시지를 소비합니다. 특정 오프셋부터 소비하려면 먼저 Consumer Group을 생성하고 해당 오프셋을 설정해야 합니다.

### SLS 연동

1.  Alibaba Cloud(알리바바 클라우드)에서 Kafka 프로토콜 기반 소비를 활성화해야 합니다.

### CLS 연동

1.  CLS 자동 샤딩 기능을 비활성화하세요.
2.  필요한 리소스의 AK & SK를 신청하세요.

## 4\. LogBus2 설치 및 업그레이드

### 설치 방법

1.  LogBus2 설치 패키지를 다운로드한 후 압축을 해제합니다.
2.  압축 해제 후 디렉터리 구조는 다음과 같습니다.

📂 **LogBus2 디렉터리 구조**

- `logbus`: LogBus2 실행 바이너리
- `conf`:
  - `daemon.json`: 설정 파일 템플릿
- `tools`:
  - `configConvert`: 설정 변환 도구

### 업데이트

**업데이트 요구사항:** LogBus2 버전 ≥ 2.0.1.7

**업데이트 방법**

```bash
./logbus update
```

위 명령어를 실행하면 업그레이드가 완료됩니다. 이후 다음 명령어로 LogBus2를 시작하세요.

```bash
./logbus start
```

## 5\. LogBus2 사용 및 설정

### 실행 명령어

**LogBus2 시작**

```bash
./logbus start
```

**LogBus2 중지**

```bash
./logbus stop
```

**LogBus2 재시작**

```bash
./logbus restart
```

**설정 및 TE 시스템 연결 상태 확인**

```bash
./logbus env
```

**LogBus 읽기 기록 초기화**

```bash
./logbus reset(Kafka가 현재 사용 불가 상태일 경우 실행 불가)
```

**전송 진행 상태 확인**

```bash
./logbus progress(Kafka가 현재 사용 불가 상태일 경우 실행 불가)
```

**파일 형식 확인**

```bash
./logbus dev(Kafka가 현재 사용 불가 상태일 경우 실행 불가)
```

### 설정 파일 가이드

**기본 구성 템플릿**

```json
{
  "datasource": [
    {
      "file_patterns": [
        "/data/log1/*.txt", // 유저가 업로드할 원본 데이터 파일의 절대 경로로 변경 필요
        "/data/log2/*.log"
      ], // 파일 매칭 패턴
      "app_id": "app_id" // TE 웹사이트에서 발급된 APP ID (TE 프로젝트 설정 페이지에서 확인 후 입력)
    }
  ],
  "push_url": "http://RECEIVER_URL" // (SaaS) 전송 시 기본 URL: https://te-receiver-naver.thinkingdata.kr/
  // 프라이빗 배포 환경에서는 해당 URL을 데이터 전송 서버 주소로 변경해야 합니다.
}
```

**자주 사용하는 설정**

**파일 업로드 설정**

```json
{
  "datasource": [
    {
      "type": "file",
      "file_patterns": ["/data/log1/*.txt", "/data/log2/*.log"], // 파일 경로 패턴 (Glob 매칭)
      "app_id": "app_id", // TE 웹사이트에서 발급된 APP ID (TE 프로젝트 설정 페이지에서 확인 후 입력)
      "unit_remove": "day", // 파일 삭제 단위 ("day" 또는 "hour" 지원)
      "offset_remove": 7, // unit_remove * offset_remove로 최종 삭제 시간 결정 (0보다 커야 적용됨)
      "remove_dirs": true, // 모든 파일 소비 완료 시 해당 디렉터리 삭제 (기본값: false)
      "http_compress": "gzip" // HTTP 압축 사용 여부 ("none" 또는 "gzip")
    }
  ],
  "cpu_limit": 4, // LogBus2가 사용할 최대 CPU 코어 수 제한
  "push_url": "http://RECEIVER_URL"
}
```

**Kafka 설정**

```json
{
  "datasource": [
    {
      "type": "kafka", // 데이터 유형: Kafka
      "topic": "ta", // 소비할 Kafka 토픽
      "brokers": [
        "localhost:9091" // Kafka 브로커 주소
      ],
      "consumer_group": "logbus", // 소비자 그룹 이름
      "cloud_provider": "ali", // 클라우드 제공업체 ("ali", "tencent", "huawei" 지원)
      "username": "", // Kafka 사용자명
      "password": "", // Kafka 인증 비밀번호
      "instance": "", // 클라우드 인스턴스 이름
      "protocol": "none", // 인증 프로토콜 ("none", "plain", "scramsha256", "scramsha512" 지원)
      "block_partitions_revoked": true,
      "app_id": "YOUR_APP_ID"
    }
  ],
  "cpu_limit": 4, // LogBus2가 사용할 최대 CPU 코어 수 제한
  "push_url": "http://RECEIVER_URL"
}
```

**SLS 설정**
**⚠️ SLS 소비를 사용하기 전에 Alibaba Cloud에서 SLS Kafka 소비 프로토콜을 활성화해야 합니다.**

```json
{
  "datasource": [
    {
      "type": "kafka",
      "brokers": ["{PROJECT}.{ENTRYPOINT}:{PORT}"], // 브로커 주소 (자세한 내용은 https://help.aliyun.com/document_detail/29008.htm 참고)
      "topic": "{SLS_Logstore_NAME}", // Logstore 이름
      "protocol": "plain",
      "consumer_group": "{YOUR_CONSUMER_GROUP}", // 소비자 그룹 이름
      "username": "{PROJECT}", // 프로젝트 이름
      "disable_tls": true,
      "password": "{ACCESS_ID}#{ACCESS_PASSWORD}", // Alibaba Cloud RAM 권한 인증 정보
      "app_id": "YOUR_APP_ID"
    }
  ],
  "push_url": "http://RECEIVER_URL"
}
```

**CLS 설정**
**⚠️ 사용 전에 소비/쓰기 처리량이 로그 보존 시간을 초과하지 않도록 확인하세요.**

```json
{
  "datasource": [
    {
      "type": "kafka",
      "brokers": ["YOUR_AZ_ENDPOINT"],
      "session_timeout": 9000,
      "fetch_max_bytes": 104857600,
      "topic": "YOUR_TOPIC",
      "protocol": "plain",
      "consumer_group": "YOUR_GROUP",
      "username": "",
      "password": "",
      "block_partitions_revoked": "true",
      "app_id": "YOUR_APP_ID"
    }
  ],
  "push_url": "http://RECEIVER_URL"
}
```

### 전체 설정 항목

#### 설정 항목 및 설명

| 설정 항목             | 유형        | 예시 값               | 필수 여부 | 설명                                                                                                                          |
| :-------------------- | :---------- | :-------------------- | :-------- | :---------------------------------------------------------------------------------------------------------------------------- |
| `cpu_limit`           | Number      | 4                     | ❌        | LogBus2가 사용할 최대 CPU 코어 수 제한                                                                                        |
| `push_url`            | String      | "http://RECEIVER_URL" | ✔️        | 데이터 전송을 위한 수신 서버(Receiver) 주소 (http/https 필수)                                                                 |
| `datasource`          | Object list | -                     | ✔️        | 데이터 소스 리스트                                                                                                            |
| `min_disk_free_space` | uint64      | 1024                  | ❌        | LogBus2 실행 디렉터리의 최소 사용 가능 디스크 공간(KB). 설정값보다 적을 경우 자동 종료됨 (기본값: 1 \* 1024 \* 1024 KB = 1GB) |

#### datasource (데이터 소스 설정: 파일 업로드)

**파일**

| 설정 항목            | 유형        | 예시 값                               | 필수 여부 | 기본값   | 설명                                                                                                                                                                 |
| :------------------- | :---------- | :------------------------------------ | :-------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app_id`             | String      | "YOUR_APP_ID"                         | ✔️        | ""       | 데이터 업로드 대상 프로젝트 APP ID                                                                                                                                   |
| `appid_in_data`      | Bool        | `true` / `false`                      | ❌        | `false`  | 파일 내 포함된 `appid` 값을 사용하여 데이터 분배할 경우 `true`로 설정 (설정 시 `app_id` 필드 미사용)                                                                 |
| `specified_push_url` | Bool        | `true` / `false`                      | ❌        | `false`  | `true`: `push_url`을 그대로 사용하여 전송 (http://yourhost:yourport) <br> `false`: `push_url`을 분석하여 LogBus2 URL 형식으로 전송 (http://yourhost:yourport/logbus) |
| `add_uuid`           | Bool        | `true` / `false`                      | ❌        | `false`  | `true` 설정 시 각 데이터에 UUID 속성 추가 (단, 성능 저하 가능)                                                                                                       |
| `file_patterns`      | String list | ["/data/logs/\*.log", "/data/\*.txt"] | ✔️        | [""]     | 업로드할 파일 경로 (와일드카드 지원, 정규식 미지원) <br> 기본적으로 `.gz` / `.iso` / `.rpm` / `.zip` / `.bz` / `.rar` / `.bz2` 확장자는 무시됨                       |
| `ignore_files`       | String list | ["/data/logs/ignore.log"]             | ❌        | [""]     | `file_patterns` 내에서 업로드 제외할 파일 목록                                                                                                                       |
| `unit_remove`        | String      | "day" / "hour"                        | ❌        | ""       | 업로드 후 파일 자동 삭제 기준 (일 "day" 또는 시간 "hour") <br> 설정하지 않으면 파일이 자동 삭제되지 않아 메모리 사용량 증가 가능                                     |
| `offset_remove`      | Int         | 7                                     | ❌        | 0        | `unit_remove` 설정 시 유효, 파일 유지 기간 (예: "day" 설정 후 7이면 7일 후 삭제)                                                                                     |
| `remove_dirs`        | Bool        | `true` / `false`                      | ❌        | `false`  | 디렉터리 내 모든 파일이 처리 완료된 후 디렉터리 삭제 여부                                                                                                            |
| `http_timeout`       | String      | "500ms", "60s", "10m"                 | ❌        | "600s"   | Receiver로 데이터 전송 시 타임아웃 설정 <br> 범위: 200ms \~ 600s (지원 단위: "ms", "s", "m", "h")                                                                    |
| `iops`               | int         | 20000                                 | ❌        | 20000    | LogBus2의 초당 데이터 처리량 제한 (건수 기준)                                                                                                                        |
| `limit`              | bool        | `true` / `false`                      | ❌        | `false`  | `true` 설정 시 전송 속도 제한 활성화                                                                                                                                 |
| `http_compress`      | String      | "none" / "gzip"                       | ❌        | "none"   | HTTP 전송 시 데이터 압축 방식 <br> "none": 압축 안 함 (기본값) <br> "gzip": Gzip 압축                                                                                |
| `filters`            | Object list | -                                     | ❌        | -        | 이벤트 필터 설정 (복수 필터 사용 시 OR 연산 적용)                                                                                                                    |
| `filters[0].key`     | String      | "\#event_name"                        | ✔️        | -        | 필터링할 키 값                                                                                                                                                       |
| `filters[0].value`   | Interface{} | "register"                            | ✔️        | -        | 필터링할 값                                                                                                                                                          |
| `filters[0].type`    | String      | "string"                              | ❌        | "string" | 필터링할 값의 데이터 타입 <br> 지원 타입: "string", "boolean", "int64", "regex"                                                                                      |

#### Kafka 설정

**⚠️ Kafka 모드를 사용하기 전에 반드시 Consumer Group의 자유 사용 기능을 활성화해야 합니다.**

| 설정 항목                  | 유형        | 예시 값            | 필수 여부 | 기본값     | 설명                                                                                                               |
| :------------------------- | :---------- | :----------------- | :-------- | :--------- | :----------------------------------------------------------------------------------------------------------------- |
| `brokers`                  | String List | ["localhost:9092"] | ✔️        | [""]       | Kafka Brokers 주소 목록                                                                                            |
| `topic`                    | String      | "ta-msg-chan"      | ✔️        | ""         | Kafka 소비(Consume)할 토픽                                                                                         |
| `consumer_group`           | String      | "ta-consumer"      | ✔️        | ""         | Kafka Consumer Group 이름                                                                                          |
| `protocol`                 | String      | "plain"            | ❌        | "none"     | Kafka 인증 방식 ("none", "plain", "scramsha256", "scramsha512" 지원)                                               |
| `username`                 | String      | "ta-user"          | ❌        | ""         | Kafka 사용자명                                                                                                     |
| `password`                 | String      | "ta-password"      | ❌        | ""         | Kafka 비밀번호                                                                                                     |
| `instance`                 | String      | ""                 | ❌        | ""         | CKafka(Cloud Kafka) 사용 시 인스턴스 ID 필요                                                                       |
| `fetch_count`              | Number      | 1000               | ❌        | 10000      | 한 번의 Poll에서 가져올 메시지 개수                                                                                |
| `fetch_time_out`           | Number      | 30                 | ❌        | 5          | Poll 타임아웃(초 단위)                                                                                             |
| `read_committed`           | Bool        | `true`             | ❌        | `false`    | `true`: Kafka에서 Uncommitted 데이터 소비 허용                                                                     |
| `disable_tls`              | Bool        | `true`             | ❌        | `false`    | `true`: TLS 인증 비활성화                                                                                          |
| `cloud_provider`           | String      | "tencent"          | ❌        | ""         | 클라우드 Kafka 사용 시 설정 필요 <br> 지원 클라우드: "tencent", "huawei", "ali"                                    |
| `block_partitions_revoked` | Bool        | `false`            | ❌        | `false`    | `true`: Consumer Group 내 여러 LogBus 인스턴스가 있을 경우, 중복 소비 방지                                         |
| `auto_reset_offset`        | String      | "earliest"         | ❌        | "earliest" | Consumer Group의 초기 Offset 설정 <br> "earliest": 가장 오래된 메시지부터 소비 <br> "latest": 최신 메시지부터 소비 |

**⚠️ 참고:** LogBus2는 Kafka를 부하 분산(Load Balancing) 방식으로 소비합니다. 따라서 LogBus2 인스턴스 개수는 Kafka 파티션 개수보다 크지 않아야 합니다.

#### Kafka 모니터링 및 대시보드 설정

- 모니터링 설정 및 대시보드 구축 방법: Monitoring Configuration DEMO
- 알림(경고) 설정: Alert Configuration DEMO
- Kafka 플러그인 사용법: Plugin Configuration DEMO

## 6\. 고급 사용법

### 단일 LogBus로 여러 이벤트 전송

단일 LogBus 인스턴스를 사용할 경우, I/O 제한으로 인해 일부 로그가 지연되어 소비될 수 있습니다.
예를 들어, LogBus가 아래 순서대로 파일을 소비한다고 가정합니다.

```
event_*/log.1 → event_*/log.2 → event_*/log.3
```

이 경우, 특정 로그 파일의 소비 속도가 느려질 수 있습니다.
이를 해결하기 위해 여러 개의 LogBus를 실행하여, 특정 컨텍스트가 필요 없는 로그를 Glob 패턴을 이용해 병렬로 업로드하는 방식을 적용할 수 있습니다.

### 여러 개의 파이프라인(Pipeline) 설정

**⚠️ 주의:** 여러 개의 Pipeline을 설정할 경우, 각 Pipeline의 `app_id`는 중복될 수 없습니다.

```json
{
  "datasource": [
    {
      "file_patterns": ["/data/log1/*.txt", "/data/log2/*.log"], // 파일 경로 패턴 (Glob 지원)
      "app_id": "app_id_1", // TE 웹사이트에서 발급된 APP ID
      "unit_remove": "day", // 파일 삭제 단위 ("day" 또는 "hour" 지원)
      "offset_remove": 7, // unit_remove * offset_remove로 최종 삭제 시간 결정 (0보다 커야 적용됨)
      "remove_dirs": true, // 디렉터리 삭제 여부 (모든 파일이 처리된 후 삭제)
      "http_compress": "gzip" // HTTP 압축 형식 ("none" 또는 "gzip")
    },
    {
      "file_patterns": ["/data/log3/*.txt", "/data/log4/*.log"], // 다른 파일 패턴 적용
      "app_id": "app_id_2", // 두 번째 Pipeline의 APP ID (중복 불가)
      "unit_remove": "day",
      "offset_remove": 7,
      "remove_dirs": true,
      "http_compress": "gzip"
    }
  ],
  "cpu_limit": 4, // LogBus2가 사용할 CPU 코어 수 제한
  "push_url": "http://RECEIVER_URL"
}
```

### LogBus2 Docker 환경에서 실행하기

**1. 최신 LogBus2 Docker 이미지 다운로드**

```bash
docker pull thinkingdata/ta-logbus-v2:latest
```

**2. 로컬 환경에 설정 파일 및 디렉터리 생성**

```bash
mkdir -p /your/folder/path/{conf,log,runtime}
touch /your/folder/path/daemon.json
vim /your/folder/path/daemon.json
```

**⚠️ 경고:** `runtime` 디렉터리 내 파일을 임의로 삭제하지 마세요.

**3. 설정 파일 (daemon.json) 작성**
아래 설정 파일을 `/your/folder/path/conf/daemon.json`에 저장하세요.

```json
{
  "datasource": [
    {
      "type": "file",
      "app_id": "YOUR_APP_ID",
      "file_patterns": ["/test-data/*.json"]
    },
    {
      "type": "kafka",
      "app_id": "YOUR_APP_ID",
      "brokers": ["localhost:9092"],
      "topic": "ta-message",
      "consumer_group": "ta"
    }
  ],
  "push_url": "YOUR_PUSH_URL" // "/logbus" 접미사를 포함하지 않은 URL 입력
}
```

**4. LogBus2 컨테이너 실행**

```bash
docker run -d \
  --name logbus-v2 \
  --restart=always \
  -v /your/data/folder:/test-data/ \
  -v /your/folder/path/conf/:/ta/logbus/conf/ \
  -v /your/folder/path/log/:/ta/logbus/log/ \
  -v /your/folder/path/runtime/:/ta/logbus/runtime/ \
  thinkingdata/ta-logbus-v2:latest
```

위 명령어는 LogBus2를 백그라운드에서 실행하며, 컨테이너가 중지되더라도 자동으로 다시 시작됩니다.

### LogBus2 Kubernetes(K8s) 배포 가이드

**1. 환경 준비**
배포 전에 아래 환경이 준비되어 있어야 합니다.

✅ **필수 조건**

1.  `kubectl`이 K8s 클러스터에 연결되어 있으며, 배포 권한이 있어야 합니다.
2.  `Helm`이 로컬 환경에 설치되어 있어야 합니다. (설치 가이드 참고)

**2. LogBus2 Helm 파일 다운로드 및 설정**

1.  LogBus2 Helm 파일 다운로드
    🚀 **다운로드 링크:** Download Link

<!-- end list -->

```bash
tar xvf logBusv2-helm.tar && cd logbusv2
```

2.  LogBus2 설정 준비
    ✅ **필수 확인 사항**

<!-- end list -->

1.  K8s Persistent Volume Claim(PVC) 생성
2.  PVC 이름 및 사용 중인 네임스페이스(namespace) 확인
3.  TE 시스템의 `app_id` 및 `receiver_url` 확인

**3. `values.yaml` 설정 파일 수정**
K8s에 배포할 LogBus2 설정을 `values.yaml` 파일에 입력합니다.

```yaml
pvc:
  name: your-pvc-name # PVC 이름

logbus_version: 2.1.0.2 # 사용할 LogBus2 버전

namespace: your-namespace # 네임스페이스 이름

logbus_configs:
  - push_url: "http://your-receiver-url" # TE 데이터 수신 URL
    datasource:
      - file_patterns:
          - "container:/path/to/logs/*.log" # 컨테이너 내부 로그 파일 경로 (주의: "container:" 프리픽스 유지)
          - "container:/path/to/logs/*.json"
        app_id: "your-app-id" # TE 시스템의 APP ID
```

**4. LogBus2 배포**

1.  배포 전 YAML 미리보기 (테스트 실행)

<!-- end list -->

```bash
helm install --dry-run -f values.yaml logbus .
(이 명령어는 실제 배포 없이 설정 내용을 미리 확인하는 용도입니다.)
```

2.  Helm을 이용한 LogBus2 배포

<!-- end list -->

```bash
helm install -f values.yaml logbus-v2 .
```

3.  배포된 StatefulSet 확인

<!-- end list -->

```bash
kubectl get statefulset
```

4.  생성된 Pod 확인

<!-- end list -->

```bash
kubectl get pods
```

**5. K8s 환경에서 LogBus2 버전 업데이트**

1.  `values.yaml` 수정 (버전 변경)

<!-- end list -->

```bash
vim values.yaml
```

💡 기존 `logbus_version` 값을 최신 버전으로 변경

```yaml
logbus_version: 2.0.1.8  # 이전 버전
↓
logbus_version: 2.1.0.2  # 최신 버전
```

**⚠️ 주의:** 최신 버전 사용 시 `latest` 태그를 직접 사용하지 않는 것이 좋습니다.
버전 호환성 문제를 피하기 위해 명시적인 버전 번호를 사용하는 것이 권장됩니다.

2.  Helm을 이용한 LogBus2 업그레이드

<!-- end list -->

```bash
helm upgrade -f values.yaml logbus .
```

이후 K8s가 자동으로 롤링 업데이트(Rolling Update)를 수행하므로, 업데이트가 완료될 때까지 기다립니다.

**⚠️ 주의 사항**

1.  LogBus2가 마운트된 PVC에 대한 읽기/쓰기 권한을 가져야 합니다.
2.  LogBus2는 파일 소비 기록과 실행 로그를 개별 Pod별로 PVC에 저장합니다.
    - 만약 PVC가 삭제되면 LogBus 관련 데이터가 사라져 중복 전송(재전송) 문제가 발생할 수 있습니다.
    - 따라서, PVC 삭제 전 반드시 데이터를 백업해야 합니다.

#### LogBus2 설정 확인 및 상세 설명

1.  현재 사용 가능한 설정 확인 (Helm 명령어 실행)

<!-- end list -->

```bash
helm show values .
```

2.  기본 설정 (values.yaml) 예시

<!-- end list -->

```yaml
# PVC 설정
pvc:
  name: pvc-logbus # PVC 이름

# LogBus2 버전
logbus_version: 2.1.0.2

# 네임스페이스
namespace: big-data

# LogBus2 Pod 개별 설정
logbus_configs:
  #### Pod 1 설정
  - push_url: "http://172.17.16.6:8992/" # TE 데이터 수신 URL
    datasource:
      - file_patterns:
          #### PVC 내 로그 파일 상대 경로 (Pod 1)
          - "container:/ta-logbus-0/data_path/*"
        #### TE 프로젝트 APP ID
        app_id: "thinkingAnalyticsAppID"

  #### Pod 2 설정
  - push_url: "http://172.26.18.132:8992/"
    datasource:
      - file_patterns:
          - "container:/ta-logbus-1/data_path/*"
        app_id: "thinkingAnalyticsAppID"

  #### Pod 3 설정
  - push_url: "http://172.26.18.132:8992/"
    datasource:
      - file_patterns:
          - "container:/ta-logbus-2/data_path/*"
        app_id: "thinkingAnalyticsAppID"
# LogBus2 리소스 요청 (필수는 아님, 필요 시 활성화)
# requests:
#   cpu: 2
#   memory: 1Gi
```

#### PVC 및 네임스페이스 설정

```yaml
pvc:
  name: 실제 PVC 이름

namespace: 기존 네임스페이스 이름

logbus_configs:
  - push_url: "http://your-te-receiver-url" # TE Receiver URL (http/https 필수)
    datasource:
      - file_patterns:
          - "container:/ta-logbus-0/data_path/*" # 파일 경로 (container: 프리픽스 필수)
        app_id: "thinkingAnalyticsAppID" # TE 시스템 APP ID
```

🚀 **파일 경로 설정 시 주의할 점:**

- `"container:"` 프리픽스는 배포 과정에서 자동으로 컨테이너가 접근할 수 있는 절대 경로로 변환됩니다.
- 따라서, 디렉터리 설정 시 **반드시** `"container:"` 프리픽스를 포함해야 합니다.

#### PVC 내 여러 디렉토리 처리

✅ **권장 방식:**

- PVC 내 여러 디렉터리를 처리할 경우, 각 디렉터리를 개별 Pod에서 처리하는 것이 성능과 안정성 측면에서 더 유리합니다.
- 각 Pod가 서로 다른 파일 경로를 감지 및 처리하도록 구성하면 병렬 처리 성능이 향상됩니다.

**PVC 내 다중 디렉터리 설정 예시**

```yaml
pvc:
  name: pvc-logbus # PVC 이름

namespace: big-data # 네임스페이스

logbus_configs:
  #### Pod 1 - 첫 번째 디렉터리 처리
  - push_url: "http://172.17.16.6:8992/" # TE Receiver URL (http/https 필수)
    datasource:
      - file_patterns:
          - "container:/ta-logbus-0/data_path/*" # Pod 1이 처리할 디렉터리
        app_id: "thinkingAnalyticsAppID"

  #### Pod 2 - 두 번째 디렉터리 처리 (각 app_id 및 push_url 개별 설정 필요)
  - push_url: "http://172.26.18.132:8992/"
    datasource:
      - file_patterns:
          - "container:/ta-logbus-1/data_path/*"
        app_id: "thinkingAnalyticsAppID"

  #### Pod 3 - 세 번째 디렉터리 처리
  - push_url: "http://172.26.18.132:8992/"
    datasource:
      - file_patterns:
          - "container:/ta-logbus-2/data_path/*"
        app_id: "thinkingAnalyticsAppID"
```

#### 여러 PVC 처리 방법

✅ **현재 LogBus2는 단일 PVC 배포만 지원합니다.**

- 여러 PVC를 사용하려면 각 PVC별로 `values.yaml` 파일을 따로 생성하여 개별 배포해야 합니다.
- 즉, PVC마다 별도의 Helm 배포를 수행해야 합니다.

## 7\. 자주 묻는 질문 (FAQ)

**Q1. 폴더 자동 삭제 기능을 활성화했지만, LogBus가 폴더를 삭제하지 않습니다.**
A: LogBus가 폴더를 삭제하려면 다음 조건이 충족되어야 합니다.

1.  해당 폴더 내의 모든 파일이 LogBus에 의해 **완전히 처리된 상태**여야 합니다.
2.  폴더 내에 **단 하나의 파일도 남아 있지 않아야 합니다.**

**Q2. 로그 데이터가 업로드되지 않는 이유는 무엇인가요?**
A:

1.  파일 내 개별 데이터 항목에 줄 바꿈 문자(개행문자 `\n`)가 포함되어 있는지 확인하세요.
    - LogBus는 개별 데이터 항목 내 개행문자를 허용하지 않습니다.
2.  파일 경로 패턴이 올바르게 설정되었는지 확인하세요.
    - LogBus의 `file_patterns` 설정은 **정규식(Regex)이 아니라 와일드카드(Glob)만 지원**합니다.
    - 예를 들어, `*.log` 패턴을 사용하면 `/data/log1/test.log` 파일이 매칭됩니다.
3.  파일이 LogBus가 접근할 수 있는 위치에 있는지 확인하세요.
    - 컨테이너 내에서 올바른 경로로 마운트되었는지 확인해야 합니다.

**Q3. 파일이 중복 업로드되는 이유는 무엇인가요?**
A:

1.  파일 내 데이터 항목에 개행문자(`\n`)가 포함되지 않았는지 확인하세요.
2.  파일 패턴이 정확하게 매칭되는지 확인하세요.
    - `file_patterns` 설정은 **정규식이 아닌 Glob 패턴만 지원**합니다.
    - 잘못된 설정이 있을 경우, LogBus가 동일한 파일을 여러 번 처리할 수 있습니다.

**Q: Q4. 데이터가 특정 서버에 집중되는(데이터 스큐) 이유는 무엇인가요?**
A:

- TE 시스템은 `distinct_id`를 기준으로 데이터를 분산(Shuffle) 처리합니다.
- 대량의 데이터에서 **동일한 `distinct_id` 값이 반복적으로 사용**될 경우, 특정 노드에서 처리 부담이 증가하여 데이터 불균형(데이터 스큐)이 발생할 수 있습니다.
- 이를 방지하려면, `distinct_id` 값을 더 균등하게 분포되도록 생성해야 합니다.
