from flask import Flask, request

app = Flask(__name__)

@app.route("/callback", methods=["GET"])
def callback():
    # 接收快手回调全部参数
    code = request.args.get("code")
    state = request.args.get("state")
    full_query = request.query_string.decode("utf-8")

    print("========================================")
    print("收到回调请求")
    print(f"完整参数串: {full_query}")
    print(f"code: {code}")
    print(f"state: {state}")
    print("========================================\n")

    # 返回简单文本表示接收成功
    return "receive ok", 200

if __name__ == "__main__":
    # 关键：0.0.0.0 允许局域网/FRP转发访问
    app.run(host="0.0.0.0", port=8700, debug=False)