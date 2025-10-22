# 데이터 업로드 가이드

LogBus2를 사용하여 생성된 데이터를 ThinkingEngine으로 업로드하는 방법을 안내합니다.

## 사전 준비

1. **LogBus2 바이너리**: `logbus 2/` 디렉터리에 있는 LogBus2 실행 파일
2. **ThinkingEngine 정보**:
   - APP ID: ThinkingEngine 프로젝트의 APP ID
   - Receiver URL: 데이터 전송을 위한 Receiver 주소

## 사용 방법

### 1. 기본 사용법

```bash
python -m data_generator.main upload \
  --data-file ./data_generator/output/logs_20251022_155706.jsonl \
  --app-id YOUR_APP_ID \
  --push-url https://te-receiver-naver.thinkingdata.kr/
```

### 2. 전체 옵션

```bash
python -m data_generator.main upload \
  --data-file ./data_generator/output/logs_20251022_155706.jsonl \  # 업로드할 데이터 파일
  --app-id YOUR_APP_ID \                                             # ThinkingEngine APP ID
  --push-url https://te-receiver-naver.thinkingdata.kr/ \           # Receiver URL
  --logbus-path "./logbus 2/logbus" \                               # LogBus2 바이너리 경로 (기본값)
  --cpu-limit 4 \                                                    # CPU 코어 수 제한
  --compress \                                                       # Gzip 압축 사용 (기본값)
  --auto-remove \                                                    # 업로드 후 파일 자동 삭제
  --remove-after-days 7 \                                           # 삭제 기간 (일)
  --monitor-interval 5 \                                            # 모니터링 간격 (초)
  --no-auto-stop                                                    # 업로드 후 LogBus 자동 중지 안 함
```

### 3. 옵션 설명

| 옵션 | 단축 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `--data-file` | `-f` | ✅ | - | 업로드할 데이터 파일 경로 (.jsonl) |
| `--app-id` | `-a` | ✅ | - | ThinkingEngine APP ID |
| `--push-url` | `-u` | ✅ | - | ThinkingEngine Receiver URL |
| `--logbus-path` | `-l` | ❌ | `./logbus 2/logbus` | LogBus2 바이너리 경로 |
| `--cpu-limit` | - | ❌ | `4` | CPU 코어 수 제한 |
| `--compress` | - | ❌ | `True` | Gzip 압축 사용 |
| `--auto-remove` | - | ❌ | `False` | 업로드 후 파일 자동 삭제 |
| `--remove-after-days` | - | ❌ | `7` | 파일 삭제 기간 (일) |
| `--monitor-interval` | - | ❌ | `5` | 모니터링 간격 (초) |
| `--no-auto-stop` | - | ❌ | `False` | 업로드 후 LogBus 자동 중지 안 함 |

## 사용 예시

### 예시 1: 기본 업로드

```bash
python -m data_generator.main upload \
  -f ./data_generator/output/logs_20251022_155706.jsonl \
  -a "your_app_id_here" \
  -u "https://te-receiver-naver.thinkingdata.kr/"
```

### 예시 2: 자동 파일 삭제 활성화

업로드 후 7일이 지나면 파일을 자동으로 삭제합니다.

```bash
python -m data_generator.main upload \
  -f ./data_generator/output/logs_20251022_155706.jsonl \
  -a "your_app_id_here" \
  -u "https://te-receiver-naver.thinkingdata.kr/" \
  --auto-remove \
  --remove-after-days 7
```

### 예시 3: LogBus를 계속 실행 상태로 유지

업로드 후에도 LogBus를 중지하지 않습니다 (추가 파일 업로드를 위해).

```bash
python -m data_generator.main upload \
  -f ./data_generator/output/logs_20251022_155706.jsonl \
  -a "your_app_id_here" \
  -u "https://te-receiver-naver.thinkingdata.kr/" \
  --no-auto-stop
```

## 동작 원리

1. **설정 파일 생성**: `logbus 2/conf/daemon.json` 파일 생성
2. **설정 검증**: LogBus2 설정 확인
3. **LogBus2 시작**: 데이터 업로드 시작
4. **진행 상태 모니터링**: 주기적으로 업로드 상태 확인
5. **자동 중지** (선택): 업로드 완료 후 LogBus2 중지

## 주의사항

1. **절대 경로 사용**: 데이터 파일 경로는 절대 경로를 권장합니다.
2. **LogBus2 권한**: LogBus2 바이너리에 실행 권한이 있어야 합니다.
3. **네트워크 연결**: Receiver URL에 접근 가능해야 합니다.
4. **디스크 공간**: 충분한 디스크 공간이 있어야 합니다 (최소 1GB).

## 문제 해결

### LogBus2를 찾을 수 없습니다

```bash
# LogBus2 바이너리 경로를 명시적으로 지정
python -m data_generator.main upload \
  -f your_file.jsonl \
  -a YOUR_APP_ID \
  -u YOUR_URL \
  -l "/absolute/path/to/logbus"
```

### 설정 파일 검증 실패

- `logbus 2/conf/daemon.json` 파일을 확인하세요.
- APP ID와 Receiver URL이 올바른지 확인하세요.

### 업로드가 진행되지 않음

```bash
# LogBus2 상태 확인
cd "logbus 2"
./logbus env

# LogBus2 진행 상태 확인
./logbus progress
```

## LogBus2 수동 관리

필요시 LogBus2를 수동으로 관리할 수 있습니다:

```bash
cd "logbus 2"

# 시작
./logbus start

# 중지
./logbus stop

# 재시작
./logbus restart

# 상태 확인
./logbus env

# 진행 상태 확인
./logbus progress

# 읽기 기록 초기화
./logbus reset
```

## 참고 자료

- [LogBus2 공식 가이드](logbus2.md)
- ThinkingEngine 문서
