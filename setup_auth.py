import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# 사용할 API 권한 (Blogger API 쓰기 권한)
SCOPES = ['https://www.googleapis.com/auth/blogger']

def get_initial_token():
    """
    credentials.json 파일을 사용하여 처음으로 token.json을 생성합니다.
    Google Cloud Console에서 다운로드한 credentials.json 파일이 같은 폴더에 있어야 합니다.
    """
    creds = None
    
    # 1. 기존 token.json이 있는지 확인
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 2. 인증 정보가 없거나 유효하지 않으면 새로 생성
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: 'credentials.json' 파일이 없습니다.")
                print("Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 다운로드하세요.")
                return

            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # token.json 저장
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        
        print("성공: 'token.json' 파일이 생성되었습니다.")
        print("-" * 50)
        print("GitHub Actions에 등록할 시 아래 내용을 복사하여 BLOGGER_TOKEN_JSON 시크릿으로 저장하세요:")
        print(creds.to_json())
        print("-" * 50)

if __name__ == '__main__':
    get_initial_token()
