# 외부 시크릿 백엔드 참조 관례 (D14)

`access/keys.md`의 위치 참조 스킴별로 **값을 조회하지 않고 참조 실행만** 하는 관례를
정리한다. 공통 원칙: argv에 값을 절대 넣지 않는다(`ps`·셸 히스토리로 유출된다) — 값은
항상 자식 프로세스의 환경변수나 파일로만 흐르게 조립한다. 위치 참조 문자열 자체는
불투명하게 다룬다 — audit·lookup·secrets 어느 스킬도 참조를 실제로 resolve(복호·조회)
하지 않고, 형식과 사용 명령만 다룬다. 전역 `secrets_backend` 설정은 없다 — 참조(키)마다
스킴이 다를 수 있고, 한 하네스 안에 `secrets/…`와 `op://…`가 섞여 있어도 정상이다.

## `secrets/…` — 로컬 age/SOPS (secrets_mode: encrypted)

- 위치 참조 형식: `secrets/<파일>.age` 또는 `secrets/<파일>.sops.yaml`.
- 사용 명령: `sops exec-env secrets/<파일>.age '<명령>'` — 복호한 값을 `<명령>` 프로세스의
  환경변수로만 주입하고 stdout에는 찍지 않는다.
- 값을 변수에 담아 그대로 `echo`/`cat` 하지 않는다. 파일 내용을 직접 바꿔야 하면(로테이션
  반영 등) `secrets` 스킬의 편집 절차를 따른다 — `sops <파일>`은 사용자가 자신의
  터미널에서 직접 실행하고, 클로드는 대신 실행하거나 출력을 캡처하지 않는다.
- 팀 라이프사이클(온보딩·오프보딩·재키잉)은 이 문서가 아니라 `secrets` 스킬 본문을
  따른다 — 이 표는 "이미 존재하는 암호문에서 값을 안전하게 꺼내 쓰는" 사용 명령만
  다룬다.

## `op://` — 1Password

- 위치 참조 형식: `op://<vault>/<item>/<field>`.
- 사용 명령: `op run -- <명령>`(`.env`나 설정에 적힌 `op://` 참조를 통째로 해석해 자식
  프로세스 환경으로 주입) 또는 `op read op://<vault>/<item>/<field>`(값을 곧바로
  환경변수 대입에만 사용, 예: `export TOKEN=$(op read op://vault/item/field)`처럼 값을
  화면에 찍지 않고 뒤이은 명령이 그 환경변수를 참조하는 형태로만 조립한다).
- 사전 조건: `op signin`으로 세션이 이미 열려 있어야 한다 — 로그인 자체는 사용자 몫이며
  이 스킬이 자격증명을 대신 입력하지 않는다.

## `vault://` — HashiCorp Vault

- 위치 참조 형식: `vault://<mount>/<path>`(또는 `keys.md`에 mount/path를 나눠 적어도
  무방).
- 사용 명령: `vault kv get -mount=<mount> <path>` — 반드시 `VAULT_ADDR`/`VAULT_NAMESPACE`를
  환경변수 또는 `-address=`/`-namespace=` 플래그로 명시한다(원칙 6 — 현재 셸의 기본값에
  암묵적으로 의존하지 않는다). 특정 필드만 필요하면 `-field=<key>`를 더해 환경변수
  대입까지만 쓰고 화면에 그대로 출력해 보여주지 않는다.
- 인증(`vault login`)은 사용자가 사전에 구성해 둔 것을 전제한다 — 이 스킬이 토큰을 대신
  발급·저장하지 않는다.

## `aws-secretsmanager://` — AWS Secrets Manager

- 위치 참조 형식: `aws-secretsmanager://<secret-id>`.
- 사용 명령: `aws secretsmanager get-secret-value --secret-id <id> --profile <p> --region
  <r> --query SecretString --output text` — `--profile`/`--region`을 항상 명시한다(원칙
  6, 기본 프로파일·리전에 의존한 명령은 만들지 않는다). 결과는 `export X=$(...)`처럼
  셸 변수 대입까지만 하고 대화·로그에 그대로 echo하지 않는다.

## 공통 주의

- 이 문서의 어떤 명령도 값을 argv 리터럴로 넣지 않는다 — 항상 참조 실행(환경변수 주입,
  파일 출력)만 조립한다. 비밀번호 계열은 `--password`류 플래그·URL 인라인 자격증명 형태를
  절대 쓰지 않는다.
- audit·lookup은 이 참조들을 resolve하지 않는다 — audit의 `check_credentials`는 위치
  참조 컬럼이 비어 있는지만 확인하고, lookup은 위 사용 명령 안내까지만 하며 명령을 대신
  실행하거나 값을 조회·출력하지 않는다.
- 여러 백엔드가 한 하네스 안에 섞여 있는 것이 정상이다(전역 `secrets_backend` 없음) —
  `access/keys.md` 행마다 위치 참조 스킴을 보고 이 표에서 맞는 절을 찾아 명령을
  조립하면 된다.
