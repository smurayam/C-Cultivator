import requests
import subprocess
import os
import uuid

# --------------------------------------------------
# 1. Wandbox APIによるコンパイル＆実行
# --------------------------------------------------
def run_c_code(user_code: str, test_main: str):
    full_code = f"{user_code}\n\n{test_main}"
    url = "https://wandbox.org/api/compile.json"
    payload = {
        "compiler": "gcc-head-c",
        "code": full_code,
        "save": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get('status') == '0':
            return {"status": "Success", "output": result.get('program_message', '')}
        else:
            error_output = result.get('compiler_error', '') + "\n" + result.get('program_message', '')
            return {"status": "Compile/Run Error", "output": error_output.strip()}
    except Exception as e:
        return {"status": "API Error", "output": str(e)}

# --------------------------------------------------
# 2. Norminette判定処理
# --------------------------------------------------
def check_norminette(user_code: str):
    # ① UUIDを使用してプロセスごとに一意なファイル名を生成（競合回避）
    filename = f"temp_submit_{uuid.uuid4().hex[:8]}.c"
    
    # ② ユーザーコードを一時ファイルとして書き出す
    with open(filename, "w") as f:
        f.write(user_code)
    
    try:
        # ③ サブプロセスで norminette コマンドを実行
        result = subprocess.run(['norminette', filename], capture_output=True, text=True)
        output = result.stdout.strip()
        
        # ④ Norminetteの出力結果をパースする
        if "Error!" in output:
            return {"status": "Norm Error", "details": output}
        elif "OK!" in output:
            return {"status": "Norm Passed", "details": "完璧です！Normエラーはありません。"}
        else:
            return {"status": "Unknown", "details": output}
            
    except FileNotFoundError:
        return {"status": "System Error", "details": "norminette コマンドが見つかりません。"}
    except Exception as e:
        return {"status": "System Error", "details": str(e)}
    finally:
        # ⑤ 実行が終わったら必ず一時ファイルを削除する
        if os.path.exists(filename):
            os.remove(filename)

# ==========================================
# 動作テスト
# ==========================================
if __name__ == "__main__":
    # わざとNormエラーになるコード
    mock_user_code = """
char *ft_strchr(const char *s, int c) {
    while (*s) {
        if (*s == (char)c)
            return (char *)s;
        s++;
    }
    if ((char)c == '\\0')
        return (char *)s;
    return 0;
}
"""

    mock_test_main = """
#include <stdio.h>
#include <string.h>
char *ft_strchr(const char *s, int c);

int main() {
    char str[] = "42Tokyo";
    if (ft_strchr(str, 'T') == strchr(str, 'T')) {
        printf("TEST_1: OK\\n");
    } else {
        printf("TEST_1: KO\\n");
    }
    return 0;
}
"""

    print("--- 1. 機能テスト (Wandbox) ---")
    func_result = run_c_code(mock_user_code, mock_test_main)
    print(f"状態: {func_result['status']}")
    print(f"出力:\n{func_result['output']}")

    print("\n--- 2. Norminette テスト ---")
    norm_result = check_norminette(mock_user_code)
    print(f"状態: {norm_result['status']}")
    print(f"詳細:\n{norm_result['details']}")
