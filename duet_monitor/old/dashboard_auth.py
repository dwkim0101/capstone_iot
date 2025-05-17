import requests

BASE_URL = "https://smartair.site/api/auth"

class DashboardAuth:
    def __init__(self, email: str, password: str, name: str = ""):  # name은 회원가입 시만 필요
        self.email = email
        self.password = password
        self.name = name
        self.token = None

    def signup(self):
        url = f"{BASE_URL}/signup"
        data = {
            "email": self.email,
            "password": self.password,
            "name": self.name or self.email.split('@')[0]
        }
        response = requests.post(url, json=data)
        return response

    def login(self):
        url = f"{BASE_URL}/login"
        data = {
            "email": self.email,
            "password": self.password
        }
        response = requests.post(url, json=data)
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        return response

    def get_token(self):
        if not self.token:
            self.login()
        return self.token

if __name__ == "__main__":
    # 테스트용 예시
    email = "your_email@example.com"
    password = "your_password"
    name = "홍길동"

    auth = DashboardAuth(email, password, name)
    signup_resp = auth.signup()
    print("회원가입 결과:", signup_resp.status_code, signup_resp.text)

    login_resp = auth.login()
    print("로그인 결과:", login_resp.status_code, login_resp.text)
    print("발급된 토큰:", auth.get_token()) 