import requests
import json
from datetime import datetime, date

# 微信配置
appID = "wx52ece196376af6c7"
appSecret = "786f8b00fcdfa81e10d04024b58ecb58"
openId = "olf-J6lKWmyq9jiXhpU7hhtoULDk"
weather_template_id = "uGEnCn5i1L1lI3hjUVfn0e7mpksx7noJISvYlF8QyDg"

# 和风天气API Key
QWEATHER_API_KEY = "9e95521a4699479598c551c3685fac1b"


def get_city_location(city):
    """获取城市经纬度"""
    url = f"https://geoapi.qweather.com/v2/city/lookup?location={city}&key={QWEATHER_API_KEY}"
    response = requests.get(url).json()
    print("城市查询响应:", json.dumps(response, ensure_ascii=False, indent=2))
    if response['code'] == "200" and response['location']:
        return response['location'][0]['lon'], response['location'][0]['lat']
    return None, None


def get_weather(city):
    """获取天气数据（包括实时温度、日出日落等）"""
    lon, lat = get_city_location(city)
    if not lon or not lat:
        print(f"无法获取{city}的经纬度")
        return None

    # 获取实时天气
    real_time_url = f"https://devapi.qweather.com/v7/weather/now?location={lon},{lat}&key={QWEATHER_API_KEY}"
    real_time_resp = requests.get(real_time_url).json()
    print("实时天气响应:", json.dumps(real_time_resp, ensure_ascii=False, indent=2))

    # 获取每日预报（包括日出日落、最低最高温度）
    daily_url = f"https://devapi.qweather.com/v7/weather/3d?location={lon},{lat}&key={QWEATHER_API_KEY}"
    daily_resp = requests.get(daily_url).json()
    print("每日预报响应:", json.dumps(daily_resp, ensure_ascii=False, indent=2))

    if real_time_resp['code'] == "200" and daily_resp['code'] == "200":
        today = daily_resp['daily'][0]

        # 处理日出日落时间
        sunrise = today.get('sunrise', '未知')
        sunset = today.get('sunset', '未知')
        sunrise_time = sunrise.split("T")[1][:5] if "T" in sunrise else sunrise
        sunset_time = sunset.split("T")[1][:5] if "T" in sunset else sunset

        # 处理风力信息
        wind_dir_day = today.get('windDirDay', '无风向')
        wind_dir_night = today.get('windDirNight', '无风向')
        wind_scale_day = today.get('windScaleDay', '未知')
        wind_scale_night = today.get('windScaleNight', '未知')

        return {
            "city": city,
            "real_temp": real_time_resp['now']['temp'],
            "high_temp": today['tempMax'],
            "low_temp": today['tempMin'],
            "weather_day": real_time_resp['now']['text'],
            "weather_night": today['textNight'],
            "wind_dir_day": wind_dir_day,  # 只保存风向
            "wind_dir_night": wind_dir_night,  # 只保存风向
            "wind_scale_day": wind_scale_day,  # 只保存风力等级
            "wind_scale_night": wind_scale_night,  # 只保存风力等级
            "sunrise": sunrise_time,
            "sunset": sunset_time
        }
    return None


def get_access_token():
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appID}&secret={appSecret}'
    response = requests.get(url).json()
    return response.get('access_token')


def get_daily_quote():
    """使用Hitokoto API获取中文金句"""
    url = "https://v1.hitokoto.cn/?c=d&c=i&encode=text"
    response = requests.get(url)
    return response.text.strip() if response.status_code == 200 else "今日金句获取失败"


def days_to_birthday(birthday_str="1996-10-14"):
    today = date.today()
    birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
    next_birthday = birthday.replace(year=today.year)
    if next_birthday < today:
        next_birthday = next_birthday.replace(year=today.year + 1)
    return (next_birthday - today).days


def days_to_spring_festival():
    """计算到2026年春节（2026年1月25日）的天数"""
    today = date.today()
    spring_festival = date(2026, 2, 17)  # 修正为2026年春节正确日期
    return (spring_festival - today).days


def send_weather(access_token, weather_data, name="张小君"):
    today = date.today()
    today_str = today.strftime("%Y年%m月%d日")

    body = {
        "touser": openId.strip(),
        "template_id": weather_template_id.strip(),
        "url": "https://weixin.qq.com",
        "data": {
            "name": {"value": name},
            "date": {"value": today_str},
            "city": {"value": weather_data["city"]},
            "weather": {"value": f"{weather_data['weather_day']} ʕ•̫͡•ʔ"},
            "now_temperature": {"value": f"{weather_data['real_temp']}摄氏度"},
            "min_temperature": {"value": f"{weather_data['low_temp']}摄氏度"},
            "max_temperature": {"value": f"{weather_data['high_temp']}摄氏度"},
            "birthday": {"value": f"{days_to_birthday('1996-10-14')}天"},
            "diff_date1": {"value": f"{days_to_spring_festival()}天"},
            "sunrise": {"value": weather_data["sunrise"]},
            "sunset": {"value": weather_data["sunset"]},
            "textNight": {"value": weather_data["weather_night"]},
            "windDirDay": {"value": weather_data["wind_dir_day"]},  # 只显示风向
            "windDirNight": {"value": weather_data["wind_dir_night"]},  # 只显示风向
            "windScaleDay": {"value": weather_data["wind_scale_day"]},  # 只显示数字范围
            "note": {"value": get_daily_quote()}
        }
    }
    url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
    response = requests.post(url, json.dumps(body))
    print("推送响应:", json.dumps(response.text, ensure_ascii=False, indent=2))


def weather_report(city, name="张小君", birthday="1996-10-14"):
    access_token = get_access_token()
    weather_data = get_weather(city)
    if weather_data:
        print(f"天气信息： {json.dumps(weather_data, ensure_ascii=False, indent=2)}")
        send_weather(access_token, weather_data, name)
    else:
        print(f"未找到{city}的天气信息")


if __name__ == '__main__':
    weather_report("海口", "张小君", "1996-10-14")
