import os
import json
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Blogger 설정
BLOG_ID = '83709333928676025'

# RSS 피드 URL (JSON API가 더 안정적이므로 JSON으로 변경 시도)
# 만약 new-apps-we-love가 작동하지 않으면 top-free를 가져오도록 구성
RSS_FEEDS = {
    'iPhone': 'https://rss.applemarketingtools.com/api/v2/kr/apps/top-free/10/apps.json',
    'iPad': 'https://rss.applemarketingtools.com/api/v2/kr/apps/top-free/10/apps.json',
    'Mac': 'https://rss.applemarketingtools.com/api/v2/kr/apps/top-free/10/apps.json'
}

# 원래 요청하셨던 URL들 (작동 여부 확인 필요)
ORIGINAL_FEEDS = {
    'iPhone': 'https://rss.marketingtools.apple.com/api/v2/kr/apps/new-apps-we-love/10/apps.json',
    'iPad': 'https://rss.marketingtools.apple.com/api/v2/kr/ipad-apps/new-apps-we-love/10/apps.json',
    'Mac': 'https://rss.marketingtools.apple.com/api/v2/kr/mac-apps/new-apps-we-love/10/apps.json'
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

def fetch_and_format_apps(category):
    """Apple JSON API에서 앱 정보를 가져와 HTML로 포맷팅합니다."""
    # 먼저 원래 요청하신 'New Apps We Love' 시도
    url = ORIGINAL_FEEDS[category]
    print(f"{category} - '{url}' 시도 중...")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('feed', {}).get('results', [])
            if results:
                return format_results(results)
        
        print(f"{category} - 'New Apps We Love' 피드를 가져올 수 없습니다 (Status: {response.status_code}). 'Top Free' 피드로 대체합니다.")
    except Exception as e:
        print(f"{category} - 오류 발생: {e}. 'Top Free' 피드로 대체합니다.")

    # 실패 시 'Top Free' 시도
    url = RSS_FEEDS[category]
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('feed', {}).get('results', [])
            return format_results(results)
    except Exception as e:
        print(f"{category} - 대체 피드 로드 실패: {e}")
    
    return ""

def format_results(results):
    """JSON 결과를 HTML로 변환합니다."""
    apps_html = ""
    for app in results:
        title = app.get('name', 'Unknown App')
        artist = app.get('artistName', '')
        link = app.get('url', '#')
        img_url = app.get('artworkUrl100', '')
        
        apps_html += f"""
        <div style="margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 15px; display: flex; align-items: start;">
            <img src="{img_url}" style="width: 80px; height: 80px; border-radius: 18%; margin-right: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
            <div>
                <h3 style="margin: 0 0 5px 0; font-size: 18px;">{title}</h3>
                <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">{artist}</p>
                <a href="{link}" target="_blank" style="background-color: #0070c9; color: white; padding: 6px 12px; text-decoration: none; border-radius: 20px; font-weight: bold; font-size: 13px;">App Store에서 보기</a>
            </div>
        </div>
        """
    return apps_html

def post_to_blogger(service, category, content):
    """Blogger에 포스팅을 작성합니다."""
    if not content:
        print(f"{category} - 포스팅할 내용이 없어 중단합니다.")
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

    for category in RSS_FEEDS.keys():
        print(f"{category} 앱 정보를 가져오는 중...")
        content = fetch_and_format_apps(category)
        post_to_blogger(service, category, content)

if __name__ == '__main__':
    main()
