import requests
import base64
import yaml

def get_clash_config(subscription_url, output_path='clash_config.yaml'):
    response = requests.get(subscription_url)
    
    content_type = response.headers.get('Content-Type', '')

    # 检测是否是 Base64
    # if 'text/plain' in content_type or not content_type:
    try:
        decoded = base64.b64decode(response.text).decode()
        print(decoded)
        print("🔍 检测到 Base64 编码内容，需转为 YAML 配置")
        # 需要借助 subconverter 或自己写 parser
        with open(output_path, 'w') as f:
            f.write(decoded)
        print(f"✅ Base64 内容已解码并保存至 {output_path}，请用 subconverter 转为 Clash 格式")
    except Exception as e:
        print("❌ Base64 解码失败:", e)
    # elif 'yaml' in content_type or 'yml' in subscription_url:
    #     with open(output_path, 'w') as f:
    #         f.write(response.text)
    #     print(f"✅ YAML 配置已下载并保存至 {output_path}")
    # else:
    #     print("⚠️ 未知格式，请手动检查返回内容")

# 示例使用
subscription_url = 'https://45.159.48.249/subscribe?token=5cdab00b2c19a637aa676dd4fa87ac95'
get_clash_config(subscription_url, 'laomao.yaml')