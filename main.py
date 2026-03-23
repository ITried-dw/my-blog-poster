import os
import json
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Blogger 설정
BLOG_ID = '83709333928676025'

# 가장 안정적인 Apple Legacy RSS URL (JSON 포맷)
FEEDS = {
    'iPhone': 'https://itunes.apple.com/kr/rss/newapplications/limit=10/json',
    'iPad': 'https://itunes.apple.com/kr/rss/newipadapplications/limit=10/json',
    'Mac': 'https://itunes.apple.com/kr/rss/newmacapplications/limit=10/json'
}

def get_blogger_service():
    """Blogger API 서비스 객체를 생성합니다."""
    creds = None
    env_token = os.getenv('BLOGGER_TOKEN_JSON')
    
    if env_token:
        token_data = json.loads(env_token)
        creds = Credentials.from_authorized_user_info(token_data, ['https://www.googleapis.com/auth/blogger'])
    elif os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/blogger'])
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("인증 정보가 필요합니다.")
            return None
        
        if not env_token:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    return build('blogger', 'v3', credentials=creds)

def fetch_apps(category):
    """Apple Legacy API에서 앱 정보를 가져옵니다."""
    url = FEEDS[category]
    print(f"{category} 데이터 가져오는 중: {url}")
    
    try:
        # User-Agent를 설정하여 거절 방지
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"{category} 실패: HTTP {response.status_code}")
            return ""
            
        data = response.json()
        entries = data.get('feed', {}).get('entry', [])
        
        if not entries:
            print(f"{category} 데이터가 비어있습니다.")
            return ""

        apps_html = ""
        for entry in entries:
            try:
                title = entry.get('im:name', {}).get('label', 'Unknown App')
                artist = entry.get('im:artist', {}).get('label', '')
                link = entry.get('link', {}).get('attributes', {}).get('href', '#')
                # 가장 큰 이미지 (보통 index 2)
                images = entry.get('im:image', [])
                img_url = images[-1].get('label', '') if images else ''
                
                apps_html += f"""
        <div style="margin-bottom: 25px; padding: 20px; border: 1px solid #e1e4e8; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <img src="{img_url}" style="width: 70px; height: 70px; border-radius: 15px; margin-right: 15px; object-fit: cover; border: 1px solid #eee;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 4px 0; font-size: 1.2rem; color: #1a1a1a; font-weight: 700;">{title}</h3>
                    <p style="margin: 0; color: #586069; font-size: 0.95rem;">{artist}</p>
                </div>
            </div>
            <div style="display: flex; justify-content: flex-end; align-items: center; border-top: 1px solid #f1f1f1; padding-top: 15px;">
                <a href="{link}" target="_blank" style="display: inline-block; background-color: #0070c9; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 0.9rem; transition: background-color 0.2s;">App Store에서 보기</a>
            </div>
        </div>
        """
            except Exception as e:
                print(f"항목 파싱 오류: {e}")
                continue
                
        return apps_html
    except Exception as e:
        print(f"{category} 오류 발생: {e}")
        return ""

def post_to_blogger(service, category, content):
    """Blogger에 포스팅을 작성합니다."""
    if not content or len(content) < 100: # 최소 길이 체크로 빈 포스팅 방지
        print(f"{category} - 유효한 내용이 없어 포스팅을 건너뜁니다.")
        return

    today = datetime.now().strftime('%Y년 %m월 %d일')
    title = f"[{category}] 추천 앱 업데이트 - {today}"
    
    body = {
        'kind': 'blogger#post',
        'title': title,
        'content': content,
        'labels': [category]
    }
    
    posts = service.posts()
    request = posts.insert(blogId=BLOG_ID, body=body)
    response = request.execute()
    print(f"포스팅 완료: {category} - {response.get('url')}")

def main():
    service = get_blogger_service()
    if not service:
        return

    for category in FEEDS.keys():
        content = fetch_apps(category)
        post_to_blogger(service, category, content)

if __name__ == '__main__':
    main()
