import feedparser
import os
import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Blogger 설정
BLOG_ID = '83709333928676025'

# RSS 피드 URL
RSS_FEEDS = {
    'iPhone': 'https://rss.marketingtools.apple.com/api/v2/kr/apps/new-apps-we-love/10/apps.rss',
    'iPad': 'https://rss.marketingtools.apple.com/api/v2/kr/ipad-apps/new-apps-we-love/10/apps.rss',
    'Mac': 'https://rss.marketingtools.apple.com/api/v2/kr/mac-apps/new-apps-we-love/10/apps.rss'
}

def get_blogger_service():
    """Blogger API 서비스 객체를 생성합니다."""
    creds = None
    
    # GitHub Actions 환경 변수에서 토큰을 가져옵니다.
    env_token = os.getenv('BLOGGER_TOKEN_JSON')
    
    if env_token:
        # 환경 변수에서 토큰 정보 로드
        token_data = json.loads(env_token)
        creds = Credentials.from_authorized_user_info(token_data, ['https://www.googleapis.com/auth/blogger'])
    elif os.path.exists('token.json'):
        # 로컬 token.json 파일에서 로드
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/blogger'])
    
    # 인증 정보가 없거나 유효하지 않은 경우 갱신
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("인증 정보(token.json 또는 BLOGGER_TOKEN_JSON 환경 변수)가 필요합니다.")
            return None
        
        # 갱신된 인증 정보 저장 (로컬 실행 시)
        if not env_token:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

    return build('blogger', 'v3', credentials=creds)

def fetch_and_format_apps(rss_url):
    """RSS 피드에서 앱 정보를 가져와 HTML로 포맷팅합니다."""
    feed = feedparser.parse(rss_url)
    apps_html = ""
    
    for entry in feed.entries:
        title = entry.get('title', 'Unknown App')
        link = entry.get('link', '#')
        
        # 썸네일 이미지 시도 (Apple RSS 구조: feed.entries[i].im_image[2].label 등)
        # im_image는 feedparser가 자동으로 파싱하지 못할 수 있으므로 entry.summary 등을 확인
        summary = entry.get('summary', '')
        
        apps_html += f"""
        <div style="margin-bottom: 30px; border-bottom: 1px solid #eee; padding-bottom: 15px;">
            <h3 style="margin: 0 0 10px 0;">{title}</h3>
            {summary}
            <div style="margin-top: 10px;">
                <a href="{link}" target="_blank" style="background-color: #0070c9; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; font-weight: bold;">App Store에서 보기</a>
            </div>
        </div>
        """
    
    return apps_html

def post_to_blogger(service, category, content):
    """Blogger에 포스팅을 작성합니다."""
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

    for category, rss_url in RSS_FEEDS.items():
        print(f"{category} 앱 정보를 가져오는 중...")
        content = fetch_and_format_apps(rss_url)
        post_to_blogger(service, category, content)

if __name__ == '__main__':
    main()
