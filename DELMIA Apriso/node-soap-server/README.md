
# CVE-2025-6204 & CVE-2025-6205

본 문서는 SharePoint 환경에서 발생하는 **인증 없이 임의의 사용자 생성(Unauthenticated arbitrary user creation)** 및 **파일 업로드(Remote Code Execution via Authenticated File Upload)** 취약점의 모의 공격(Exploit) 및 체이닝 과정을 기록한 연구 랩 문서입니다.

<br><br><br>

## 1. 인증 없이 임의의 사용자 생성(Unauthenticated arbitrary user creation)
> 단일 취약점(CVE-2025-6205, 인가 누락)을 활용하여, 사전 인증이나 관리자 권한이 없는 외부 공격자가 시스템에 임의의 사용자를 무단으로 생성하는 취약점입니다.

<br><br>

1. **초기 접근:** 취약점이 존재하는 서버의 웹 서비스(HTTP/HTTPS) 포트에 네트워크 접근을 시도합니다. 본 취약점은 공격 발생 지점 이전에 세션이나 토큰을 통한 인증(Authentication) 과정을 요구하지 않으므로, 서버에 접근 가능한 외부 또는 내부망의 모든 사용자가 공격을 수행할 수 있습니다.



<br><br>

2. **타겟 식별:** 대상 서버가 구동 중인 애플리케이션(예: DELMIA Apriso)을 식별하고, WSDL(Web Services Description Language) 문서 조회나 디렉토리 스캐닝 등을 통해 메시지 처리를 담당하는 SOAP API 서비스가 활성화되어 있는지 확인합니다.


<br><br>

3. **엔드포인트 접근:** 비즈니스 로직(계정 생성 등) 수행 시 권한(Authorization) 검증이 누락된 취약한 특정 SOAP 통신 엔드포인트(예: /Apriso/MessageProcessor/FlexNetMessageProcessor.svc)를 타겟으로 지정하여 HTTP POST 요청을 준비합니다.


<br><br>

4. **메서드 변조:** 서버가 메시지를 정상적으로 해석할 수 있도록 HTTP 헤더의 Content-Type을 text/xml로 설정합니다. 이후 SOAP 봉투(Envelope) 및 본문(Body) 구조를 구성하고, 내부적으로 사용자 추가 기능과 연결되는 특정 메서드(예: ProcessMessageASync_v2)를 강제로 호출하도록 요청 포맷을 조작합니다.


<br><br>

5. **페이로드 주입:** 조작된 SOAP 메서드의 파라미터(xmlMessage 등) 내부에 공격자가 원하는 임의의 계정 정보(LoginName, Password, 권한 그룹 등)를 담은 XML 구조체를 주입하여 전송합니다. 서버는 요청자의 권한을 검증하지 않고 주입된 데이터를 파싱하여 데이터베이스에 그대로 반영하게 됩니다.


<br><br>

6. **실행 확인:** 페이로드 전송 후 서버로부터 정상 처리 응답(예: <tem:ProcessMessageASync_v2Result>SUCCESS</...)을 수신하는지 확인합니다. 이후 실제 서비스의 로그인 페이지(/login)로 이동하여 주입한 악성 계정 정보로 로그인을 시도하고, 정상적으로 접속 및 권한 획득이 이루어졌는지 최종 검증합니다.




<br><br><br>

## 2. 취약점 체이닝 (CVE-2025-53771 + CVE-2025-53770)
### 인증되지 않은 사용자의 역직렬화 취약점 (Unauthenticated Exploit)
> 인증 우회 취약점(CVE-2025-53771)과 역직렬화 취약점(CVE-2025-53770)을 연계하여, 로그인 없이 원격 쉘(Shell)을 획득하는 과정입니다.

<br><br>

1. **타겟 식별:** 타겟 솔루션 명과 버전(생략)을 확인하여 취약성 여부를 판별합니다.


<br><br>

2. **엔드포인트 접근:** 취약한 엔드포인트로 접근을 시도합니다.


<br><br>

3. **메서드 변조:** HTTP 요청 Method를 `GET`에서 `POST`로 변경합니다.


<br><br>

4. **체이닝 페이로드 주입:** `Referer` 헤더 조작 등을 통한 **인증 우회(Auth Bypass)** 페이로드와 **역직렬화(Deserialization)** 페이로드를 동시에 삽입하여 요청을 전송합니다.


<br><br>

5. **실행 확인:** 인증되지 않은 외부 공격자가 안전하지 않은 역직렬화를 트리거하여, 타겟 서버의 쉘 명령어 실행 권한을 탈취한 것을 최종 확인합니다.



<br><br><br>

## Credits & Authors

| Role | Author | Links |
| :--- | :--- | :--- |
| **Original Author** | J4ck3LSyN | [Website](https://jackalsyn.com) / [GitHub](https://github.com/J4ck3LSyN-Gen2) |
| **Modified & Enhanced By** | hanmin0512 | [GitHub](https://github.com/hanmin0512) |

<br><br><br>

## 취약 버전
  - Microsoft SharePoint Server Subscription Edition 16.0.18526.20508 버전 미만
  - Microsoft SharePoint Server 2019 16.0.10417.20037 버전 미만

  
> **Disclaimer**
> *This repository is a customized fork/version of the original PoC for CVE-2025-53770, modified for enhanced usability (Requests conversion, Proxy support, etc.). This documentation and the associated lab environment are strictly for educational and defensive research purposes.*
