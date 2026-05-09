import discord
from discord.ext import commands, tasks
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime, time
import random
import asyncio
import judge

# --------------------------------------------------
# 初期設定
# --------------------------------------------------
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# ⚠️ 重要: 通知を飛ばしたいチャンネルのIDをここに貼り付けてください（整数で入力）
ANNOUNCE_CHANNEL_ID = 1502152458091364445
target_time = None

# --------------------------------------------------
# データベースの初期化とダミーデータ投入
# --------------------------------------------------
def init_db():
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect('data/42_bot.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (task_id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, func_name TEXT, test_case TEXT)''')
    # 📝 変更: channel_id 列を追加
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (session_id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, channel_id INTEGER, notified_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (task_id) REFERENCES tasks(task_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS attempts (attempt_id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, user_id TEXT, started_at DATETIME, submitted_at DATETIME, status TEXT, norm_passed BOOLEAN, FOREIGN KEY (session_id) REFERENCES sessions(session_id), FOREIGN KEY (user_id) REFERENCES users(user_id))''')

    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        test_main_code = """
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
    if (ft_strchr(str, 'z') == strchr(str, 'z')) {
        printf("TEST_2: OK\\n");
    } else {
        printf("TEST_2: KO\\n");
    }
    return 0;
}
"""
        cursor.execute('''
            INSERT INTO tasks (title, description, func_name, test_case) 
            VALUES (?, ?, ?, ?)
        ''', ("ft_strchr", "標準Cライブラリの `strchr` を再実装せよ。\n\n**【プロトタイプ】**\n`char *ft_strchr(const char *s, int c);`\n\n10分以内に `/submit` に `.c` ファイルを添付して送信せよ！", "ft_strchr", test_main_code))
        print("🌱 テスト用ダミー課題をDBに投入しました！")

    conn.commit()
    conn.close()

# --------------------------------------------------
# Botのセットアップ
# --------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name} ({bot.user.id})')
    init_db()
    
    if not daily_scheduler.is_running():
        daily_scheduler.start()
        
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# --------------------------------------------------
# 🕒 ゲリラ通知システム（バックグラウンド処理）
# --------------------------------------------------
@tasks.loop(minutes=1)
async def daily_scheduler():
    global target_time
    now = datetime.now()
    
    if now.hour == 9 and now.minute == 0:
        h = random.randint(10, 21)
        m = random.randint(0, 59)
        target_time = time(h, m)
        print(f"🎲 今日の通知予定時刻を決定しました: {target_time}")

    if target_time and now.hour == target_time.hour and now.minute == target_time.minute:
        target_time = None
        await trigger_guerilla_event()

async def trigger_guerilla_event():
    channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
    if not channel:
        print("❌ 通知チャンネルが見つかりません。")
        return

    conn = sqlite3.connect('data/42_bot.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT task_id, title FROM tasks ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    task_id, task_title = row

    # --------------------------------------------------
    # 🔐 秘密の感想戦チャンネルを作成
    # --------------------------------------------------
    guild = channel.guild
    # カテゴリを探す（なければ作成）
    category = discord.utils.get(guild.categories, name="🔐 感想戦会場")
    if not category:
        category = await guild.create_category("🔐 感想戦会場")

    # @everyone は見れない、Botだけが見れる設定でチャンネル作成
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    # チャンネル名には日付と課題名を入れる
    today_str = datetime.now().strftime("%m月%d日")
    secret_channel = await guild.create_text_channel(
        name=f"{today_str}-{task_title}",
        category=category,
        overwrites=overwrites
    )
    
    # セッションを作成し、生成したチャンネルのIDも保存
    cursor.execute("INSERT INTO sessions (task_id, channel_id) VALUES (?, ?)", (task_id, secret_channel.id))
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="⚠️ ⚠️ ⚠️ ⚠️ ⚠️\nTime to Code!",
        description=f"**本日の課題が投下されました！**\n課題: `{task_title}`\n\n今すぐ `/start` コマンドを打って課題を確認してください。\n**制限時間は今から10分間です！**",
        color=0xFF0000
    )
    embed.set_footer(text="※クリアした人だけが、感想戦チャンネルに招待されます。")
    await channel.send(content="@everyone", embed=embed)

# --------------------------------------------------
# コマンド定義
# --------------------------------------------------
@bot.tree.command(name="test_alert", description="[管理者用] ゲリラ通知を今すぐテスト発射します")
async def test_alert(interaction: discord.Interaction):
    # ① サーバー内での実行かどうかをチェック（DMなら弾く）
    if interaction.guild is None:
        await interaction.response.send_message("❌ このコマンドはサーバーのチャンネル内で実行してください！", ephemeral=True)
        return

    # ② 管理者権限があるかをチェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 管理者権限が必要です。", ephemeral=True)
        return
        
    await interaction.response.send_message("通知テストを実行します...", ephemeral=True)
    await trigger_guerilla_event()

@bot.tree.command(name="ping", description="Botの生存確認と応答速度を返します")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! 🏓 ({latency}ms)')

@bot.tree.command(name="start", description="今日の課題に挑戦します（10分タイマー開始！）")
async def start(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    conn = sqlite3.connect('data/42_bot.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    
    cursor.execute('SELECT session_id, task_id FROM sessions ORDER BY session_id DESC LIMIT 1')
    session_row = cursor.fetchone()
    if not session_row:
        await interaction.response.send_message("現在アクティブな課題はありません。通知を待ってね！", ephemeral=True)
        return
    session_id, task_id = session_row
    
    cursor.execute('SELECT status FROM attempts WHERE session_id = ? AND user_id = ?', (session_id, user_id))
    attempt_row = cursor.fetchone()
    if attempt_row:
        if attempt_row[0] == 'playing':
            await interaction.response.send_message("現在挑戦中です！DMを見て `/submit` で提出してね！", ephemeral=True)
        else:
            await interaction.response.send_message("今回の課題は終了しています。", ephemeral=True)
        conn.close()
        return

    cursor.execute('SELECT title, description FROM tasks WHERE task_id = ?', (task_id,))
    task_title, task_desc = cursor.fetchone()

    try:
        embed = discord.Embed(title=f"📝 本日の課題: {task_title}", description=task_desc, color=0x00BFFF)
        embed.set_footer(text="※サーバーに戻り、 /submit コマンドでコードを提出してください。")
        await interaction.user.send(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("⚠️ DMを送信できません。", ephemeral=True)
        conn.close()
        return

    cursor.execute("INSERT INTO attempts (session_id, user_id, started_at, status) VALUES (?, ?, CURRENT_TIMESTAMP, 'playing')", (session_id, user_id))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🚀 {interaction.user.mention} が挑戦を開始しました！\nDMに課題を送信しました。10分タイマー開始！⏰")

@bot.tree.command(name="submit", description="課題のC言語コード(.cファイル)を提出します")
async def submit(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer()

    if not file.filename.endswith('.c'):
        await interaction.followup.send("❌ エラー: C言語のファイル (.c) を添付してください！")
        return

    user_id = str(interaction.user.id)
    conn = sqlite3.connect('data/42_bot.db')
    cursor = conn.cursor()

    # 📝 変更: channel_id も一緒に取得する
    cursor.execute('''
        SELECT attempt_id, started_at, tasks.test_case, sessions.channel_id
        FROM attempts 
        JOIN sessions ON attempts.session_id = sessions.session_id
        JOIN tasks ON sessions.task_id = tasks.task_id
        WHERE user_id = ? AND status = 'playing'
    ''', (user_id,))
    row = cursor.fetchone()

    if not row:
        await interaction.followup.send("❌ 現在挑戦中の課題がありません。`/start` で開始してください。")
        conn.close()
        return

    attempt_id, started_at_str, test_case, secret_channel_id = row

    started_at = datetime.strptime(started_at_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.utcnow()
    elapsed_seconds = (now - started_at).total_seconds()
    elapsed_minutes = int(elapsed_seconds // 60)
    elapsed_sec_remainder = int(elapsed_seconds % 60)
    time_str = f"{elapsed_minutes}分{elapsed_sec_remainder}秒"

    if elapsed_seconds > 600:
        cursor.execute("UPDATE attempts SET status = 'failed', submitted_at = CURRENT_TIMESTAMP WHERE attempt_id = ?", (attempt_id,))
        conn.commit()
        conn.close()
        await interaction.followup.send(f"💀 タイムアップ！ 記録: {time_str}\n10分を超過したため失格です...。")
        return

    code_bytes = await file.read()
    user_code = code_bytes.decode('utf-8')

    func_result = judge.run_c_code(user_code, test_case)
    norm_result = judge.check_norminette(user_code)

    passed = (func_result['status'] == 'Success' and "KO" not in func_result['output'])
    norm_passed = (norm_result['status'] == 'Norm Passed')
    final_status = 'cleared' if passed else 'failed'

    cursor.execute("UPDATE attempts SET status = ?, submitted_at = CURRENT_TIMESTAMP, norm_passed = ? WHERE attempt_id = ?", (final_status, norm_passed, attempt_id))
    conn.commit()
    conn.close()

    color = 0x00FF00 if passed else 0xFF0000
    embed = discord.Embed(title="📊 採点結果", color=color)
    embed.add_field(name="⏱️ クリアタイム", value=time_str, inline=False)
    
    md_ticks = "```"
    
    if passed:
        embed.add_field(name="✅ テスト結果", value="完璧に動作しました！", inline=False)
        
        # --------------------------------------------------
        # 🔐 クリア者を秘密の部屋へ招待
        # --------------------------------------------------
        if secret_channel_id:
            secret_channel = bot.get_channel(secret_channel_id)
            if secret_channel:
                # ユーザーに閲覧・書き込み権限を付与
                await secret_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
                # 部屋の中で歓迎メッセージ
                await secret_channel.send(f"🎉 {interaction.user.mention} が {time_str} でクリアして合流しました！コードを共有しよう！\n{md_ticks}c\n{user_code}\n{md_ticks}")
                # 返信Embedにチャンネルへのリンクを追加
                embed.add_field(name="🔐 感想戦会場へご案内", value=f"{secret_channel.mention} で他の人のコードを見てみよう！", inline=False)

    else:
        err_val = f"{md_ticks}text\n{func_result['output'][:1000]}\n{md_ticks}"
        embed.add_field(name="❌ エラー発生", value=err_val, inline=False)
        
    if norm_passed:
        embed.add_field(name="✅ Norminette", value="美しい！Normエラーはありません。", inline=False)
    else:
        norm_val = f"{md_ticks}text\n{norm_result['details'][:1000]}\n{md_ticks}"
        embed.add_field(name="❌ Norminette 違反", value=norm_val, inline=False)

    msg = f"🎉 **{interaction.user.mention} が課題をクリアしました！**" if passed else f"💀 **{interaction.user.mention} がテストに失敗しました...**"
    await interaction.followup.send(content=msg, embed=embed)

@bot.tree.command(name="ranking", description="現在の課題のクリアタイムランキングを表示します")
async def ranking(interaction: discord.Interaction):
    conn = sqlite3.connect('data/42_bot.db')
    cursor = conn.cursor()

    cursor.execute('SELECT session_id, task_id FROM sessions ORDER BY session_id DESC LIMIT 1')
    session_row = cursor.fetchone()
    if not session_row:
        await interaction.response.send_message("まだ課題が一度も投下されていません。", ephemeral=True)
        conn.close()
        return
    session_id, task_id = session_row

    cursor.execute('SELECT title FROM tasks WHERE task_id = ?', (task_id,))
    task_title = cursor.fetchone()[0]

    cursor.execute('''
        SELECT user_id, started_at, submitted_at, norm_passed
        FROM attempts 
        WHERE session_id = ? AND status = 'cleared'
    ''', (session_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await interaction.response.send_message("まだこの課題のクリア者はいません。一番乗りを目指そう！")
        return

    ranking_data = []
    for row in rows:
        uid, start_str, submit_str, norm = row
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        submit_dt = datetime.strptime(submit_str, "%Y-%m-%d %H:%M:%S")
        elapsed = (submit_dt - start_dt).total_seconds()
        ranking_data.append({
            'user_id': uid,
            'elapsed': elapsed,
            'norm': norm
        })

    ranking_data.sort(key=lambda x: x['elapsed'])

    embed = discord.Embed(title=f"🏆 スピードランキング - {task_title}", color=0xFFD700)
    
    medals = ["🥇", "🥈", "🥉"]
    description = ""
    for i, data in enumerate(ranking_data):
        rank_icon = medals[i] if i < 3 else f"**{i+1}位**"
        minutes = int(data['elapsed'] // 60)
        seconds = int(data['elapsed'] % 60)
        time_str = f"{minutes}分{seconds}秒"
        norm_icon = "✨(Norm完璧)" if data['norm'] else "⚠️(Norm違反)"
        
        description += f"{rank_icon} <@{data['user_id']}> : **{time_str}** {norm_icon}\n\n"

    embed.description = description
    await interaction.response.send_message(embed=embed)

# --------------------------------------------------
# 実行
# --------------------------------------------------
if __name__ == '__main__':
    bot.run(TOKEN)
