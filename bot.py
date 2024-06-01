import nextcord
from nextcord import Interaction
from nextcord.ext import commands, tasks
import requests
from datetime import datetime

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix='e/',  intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():   
    earthquake_alert.start()
    check_earthquake_report.start()
    
    print(f'✅ {bot.user.name} 已經準備好了！')

max_list = {
  1: "1 級",
  2: "2 級",
  3: "3 級",
  4: "4 級",
  5: "5 弱",
  6: "5 強",
  7: "6 弱",
  8: "6 強",
  9: "7 級"
}

last_report_id = None
@tasks.loop(seconds=5)
async def check_earthquake_report():
    global last_report_id
    response = requests.get("https://api-1.exptech.dev/api/v2/eq/report")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and data and data[0]['id'] != last_report_id:
            new_report = data[0]
            last_report_id = new_report['id']
            max_intensity = new_report['int']
            max = max_list.get(max_intensity, 'Unknown')
            embed = nextcord.Embed(title='地震報告', color=nextcord.Color.yellow())
            embed.add_field(name="#️⃣編號", value={new_report.get("id")}, inline=False)
            embed.add_field(name='🌏地點', value=f'緯度: {new_report.get("lat")} 經度: {new_report.get("lon")}', inline=False)
            embed.add_field(name='深度', value=f'{new_report.get("depth")} 公里', inline=True)
            embed.add_field(name='芮氏規模', value=new_report.get('mag'), inline=True)
            timestamp = int(new_report.get('time') / 1000)
            discord_timestamp = f"<t:{timestamp}:F>"
            embed.add_field(name='時間', value=discord_timestamp, inline=False)
            embed.add_field(name='❌震央', value=new_report.get('loc'), inline=False)
            embed.add_field(name='最大震度', value=f'{max} ', inline=False)
            embed.set_image(url=f'https://exptech.com.tw/file/images/report/{new_report.get("id")}.png')
            embed.set_footer(text='Data Provided by ExpTech')
            channel = bot.get_channel()
            await channel.send(embed=embed)
            
def get_map_image_url(lat, lon):
    return f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=10&l=map&size=650,450&pt={lon},{lat},round"

last_earthquake_id = None
@tasks.loop(seconds=1)
async def earthquake_alert():
    global last_earthquake_id
    response = requests.get("https://api-1.exptech.dev/api/v1/eq/eew?type=cwa")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list) and data:
            latest_report = data[0]
            if latest_report['id'] != last_earthquake_id:
                last_earthquake_id = latest_report['id']
                eq_data = latest_report['eq']
                timestamp = int(eq_data['time'] / 1000)
                discord_timestamp = f"<t:{timestamp}:F>"
                max_intensity = eq_data['max']
                max = max_list.get(max_intensity, 'Unknown')
                embed = nextcord.Embed(title=':warning: 地震速報 ', description=f'{discord_timestamp} 於 {eq_data.get("loc")} 發生有感地震，慎防強烈搖晃\n預估規模 `{eq_data.get("mag")}` ，震源深度 `{eq_data.get("depth")}` 公里，最大震度 {max}\由 ExpTech Studio 提供 僅供參考，請以中央氣象署資料為準\n若感受到晃動請立即**【趴下、掩護、穩住】**', color=0xFF0000)
                map_image_url = get_map_image_url(eq_data['lat'], eq_data['lon'])
                embed.set_image(url=map_image_url)
                embed.set_footer(text="Data Provided by ExpTech")
                channel = bot.get_channel()
                await channel.send(embed=embed)
                          
@bot.slash_command(name='地震報告', description='查詢最新的地震報告')
async def send_earthquake_report(interaction: Interaction):
    response = requests.get('https://api-1.exptech.dev/api/v2/eq/report')
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, list):
                data = data[0]
            if isinstance(data, dict):
                await interaction.response.defer()
                embed = nextcord.Embed(title='最新地震報告', color=nextcord.Color.yellow())
                embed.add_field(name="#️⃣編號", value={data.get("id")}, inline=False)
                embed.add_field(name='🌏地點', value=f'緯度: {data.get("lat")} 經度: {data.get("lon")}', inline=False)
                embed.add_field(name='深度', value=f'{data.get("depth")} 公里', inline=True)
                embed.add_field(name='芮氏規模', value=data.get('mag'), inline=True)
                timestamp = int(data.get('time') / 1000)
                discord_timestamp = f"<t:{timestamp}:F>"
                embed.add_field(name='時間', value=discord_timestamp, inline=False)
                embed.add_field(name='❌震央', value=data.get('loc'), inline=False)
                max_intensity = data['int']
                max = max_list.get(max_intensity, 'Unknown')
                embed.add_field(name='最大震度', value=f'{max}', inline=False)
                embed.set_image(url=f'https://exptech.com.tw/file/images/report/{data.get("id")}.png')
                embed.set_footer(text='Data Provided by ExpTech')
                await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = nextcord.Embed(title=f"❌ | {e}", color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message('目前無法查詢 API', ephemeral=True)
               
bot.run('token')
