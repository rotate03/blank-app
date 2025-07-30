import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import streamlit as st
from io import BytesIO
from PIL import Image
import time

# 设置页面配置
st.set_page_config(
    page_title="3D重力四子棋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置中文字体
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class GravityFourInARow3D:
    def __init__(self):
        # 初始化游戏状态（使用session_state确保状态持久化）
        if 'initialized' not in st.session_state:
            self.reset_game()
            st.session_state.initialized = True
        
        # 定义胜利检查方向
        self.directions = [
            (0, 1, 0), (1, 0, 0), (1, 1, 0), (1, -1, 0),
            (0, 0, 1),
            (1, 0, 1), (0, 1, 1), (1, 1, 1), 
            (1, 0, -1), (0, 1, -1), (1, 1, -1),
            (1, -1, 1), (1, -1, -1)
        ]

    def reset_game(self):
        """重置游戏状态，开始新对局"""
        st.session_state.board = np.zeros((5, 5, 5), dtype=int)
        st.session_state.heights = np.zeros((5, 5), dtype=int)
        st.session_state.current_player = 1  # 玩家1先手
        st.session_state.winner = None
        st.session_state.game_over = False
        st.session_state.move_history = []
        st.session_state.message = "新游戏开始！玩家1先行，请输入位置落子"
        st.session_state.message_color = "black"
        st.session_state.azim = 0
        st.session_state.rotation_speed = 0.5

    def slow_down(self):
        """降低旋转速度"""
        st.session_state.rotation_speed = max(0.1, st.session_state.rotation_speed - 0.5)
        
    def speed_up(self):
        """提高旋转速度"""
        st.session_state.rotation_speed = min(4.0, st.session_state.rotation_speed + 0.5)
    
    def draw_pillars(self, ax):
        """绘制棋盘柱子"""
        for x in range(5):
            for y in range(5):
                ax.plot([x, x], [y, y], [0, 4], '#95a5a6', linewidth=1.5, alpha=0.7)
    
    def draw_board(self):
        """绘制3D棋盘和棋子"""
        fig = plt.figure(figsize=(10, 8), facecolor='#f0f8ff')
        ax = fig.add_subplot(111, projection='3d')
        
        # 设置视角
        ax.view_init(elev=35, azim=st.session_state.azim)
        
        # 设置坐标轴标签
        ax.set_xticks(np.arange(0, 5, 1))
        ax.set_xticklabels(['A', 'B', 'C', 'D', 'E'])
        ax.set_yticks(np.arange(0, 5, 1))
        ax.set_yticklabels(['1', '2', '3', '4', '5'])
        ax.set_zticks(np.arange(0, 5, 1))
        ax.set_zticklabels(['1', '2', '3', '4', '5'])
        ax.set_xlabel(' 列', labelpad=15)
        ax.set_ylabel(' 行', labelpad=15)
        ax.set_zlabel(' 层', labelpad=15)
        ax.set_xlim(-0.5, 4.5)
        ax.set_ylim(-0.5, 4.5)
        ax.set_zlim(-0.5, 4.5)
        ax.grid(False)
        
        # 调整3D坐标轴比例
        ax.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([1, 1, 0.6, 1]))
        
        # 调整刻度位置
        ax.tick_params(axis='x', pad=0)
        ax.tick_params(axis='y', pad=0)
        ax.tick_params(axis='z', pad=5)
        
        # 绘制棋盘柱子
        self.draw_pillars(ax)
        
        # 绘制棋子
        x, y, z, colors = [], [], [], []
        for i in range(5):
            for j in range(5):
                for k in range(st.session_state.heights[i, j]):
                    x_val = j  # 列
                    y_val = i  # 行
                    z_val = k  # 层
                    
                    x.append(x_val)
                    y.append(y_val)
                    z.append(z_val)
                    colors.append('#e74c3c' if st.session_state.board[i, j, k] == 1 else '#3498db')
        
        # 绘制棋子
        if x:
            ax.scatter(
                x, y, z, s=250, c=colors,
                edgecolors='black', depthshade=True, alpha=0.8
            )
        
        # 如果游戏结束，显示获胜信息
        if st.session_state.game_over:
            if st.session_state.winner:
                color = '#e74c3c' if st.session_state.winner == 1 else '#3498db'
                plt.figtext(0.5, 0.95, f"玩家{st.session_state.winner}获胜！", 
                           fontsize=20, fontweight='bold', 
                           ha='center', va='center', color=color)
            else:
                plt.figtext(0.5, 0.95, "平局！", 
                           fontsize=20, fontweight='bold', 
                           ha='center', va='center', color='#555555')
        
        # 保存图形到 BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        
        # 转换为 PIL 图像并返回
        img = Image.open(buf)
        return img, buf
    
    def update_rotation(self):
        """更新视角旋转"""
        if not st.session_state.game_over:
            st.session_state.azim = (st.session_state.azim + st.session_state.rotation_speed) % 360
    
    def parse_input(self, pos_str):
        """将A1-E5格式转换为行列索引"""
        if not pos_str:
            return None, None, "请输入位置"
            
        if len(pos_str) != 2:
            return None, None, "输入格式应为字母+数字，如A1"
        
        col_char = pos_str[0].upper()
        row_char = pos_str[1]
        
        # 转换列 (A-E -> 0-4)
        if col_char not in "ABCDE":
            return None, None, "列必须为A-E之间的字母"
        col = ord(col_char) - ord('A')
        
        # 转换行 (1-5 -> 0-4)
        if row_char not in "12345":
            return None, None, "行必须为1-5之间的数字"
        row = int(row_char) - 1 
        
        return row, col, None 
    
    def make_move(self, row, col):
        """玩家在指定行列落子"""
        # 检查位置有效性
        if not (0 <= row < 5 and 0 <= col < 5):
            return False, "行列必须在有效范围内！"
        
        # 检查柱子是否已满
        if st.session_state.heights[row][col] >= 5:
            return False, "该柱子已满！"
        
        # 放置棋子
        layer = st.session_state.heights[row][col]
        st.session_state.board[row, col, layer] = st.session_state.current_player
        st.session_state.heights[row][col] += 1
        
        # 记录落子历史，用于悔棋
        st.session_state.move_history.append((row, col, layer, st.session_state.current_player))
        
        # 检查是否获胜
        if self.check_win(row, col, layer):
            st.session_state.winner = st.session_state.current_player
            st.session_state.game_over = True
            return True, f"玩家{st.session_state.current_player} 获胜！点击[重来]开始新游戏"
        
        # 检查是否平局
        if np.all(st.session_state.heights == 5):
            st.session_state.game_over = True
            return True, "平局！棋盘已满，点击[重来]开始新游戏"
        
        # 切换玩家
        st.session_state.current_player = 3 - st.session_state.current_player  # 1->2, 2->1
        return True, f"玩家{st.session_state.current_player} 请落子"
    
    def undo_move(self):
        """悔棋功能：撤销上一步操作"""
        # 检查是否有可以悔棋的步骤
        if not st.session_state.move_history:
            return "没有可悔的步骤！", "orange"
            
        # 如果游戏已经结束，悔棋后重新激活游戏
        if st.session_state.game_over:
            st.session_state.game_over = False
            st.session_state.winner = None
        
        # 取出最后一步
        last_move = st.session_state.move_history.pop()
        row, col, layer, player = last_move
        
        # 恢复棋盘状态
        st.session_state.board[row, col, layer] = 0
        st.session_state.heights[row, col] -= 1
        
        # 恢复当前玩家
        st.session_state.current_player = player
        
        return f"已悔棋，现在轮到玩家{st.session_state.current_player}落子", "blue"
    
    def check_win(self, row, col, layer):
        """检查是否有玩家获胜"""
        player = st.session_state.board[row, col, layer]
        
        # 检查每个方向
        for dx, dy, dz in self.directions:
            count = 1  # 当前位置已经有一个棋子
            
            # 正向检查
            for i in range(1, 4):
                r, c, l = row + i*dx, col + i*dy, layer + i*dz
                if not (0 <= r < 5 and 0 <= c < 5 and 0 <= l < 5):
                    break
                if st.session_state.board[r, c, l] != player:
                    break
                count += 1
            
            # 反向检查
            for i in range(1, 4):
                r, c, l = row - i*dx, col - i*dy, layer - i*dz
                if not (0 <= r < 5 and 0 <= c < 5 and 0 <= l < 5):
                    break
                if st.session_state.board[r, c, l] != player:
                    break
                count += 1
            
            if count >= 4:
                return True
        
        return False
    
    def process_move(self, text):
        """处理移动"""
        if st.session_state.game_over:
            return "游戏已结束，请点击[重来]开始新游戏", "red"
            
        row, col, error = self.parse_input(text)
        if error:
            return f"错误: {error}", "red"
        
        success, message = self.make_move(row, col)
        if not success:
            return f"错误: {message}", "red"
        else:
            return message, "green" if st.session_state.game_over else "black"

def main():
    # 初始化游戏
    game = GravityFourInARow3D()
    
    # 页面标题
    st.title("3D重力四子棋")
    
    # 创建两列布局
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 创建一个容器用于动态更新棋盘
        board_placeholder = st.empty()
        
        # 创建状态信息容器
        status_placeholder = st.empty()
    
    with col2:
        # 游戏规则
        st.subheader("游戏规则")
        rules = """
        1. 玩家轮流在5×5网格顶部落子
        2. 棋子受重力下落至最低空位
        3. 任意方向连成四子获胜
           - 水平、垂直、对角线
           - 包括3D立体对角线
        4. 输入位置格式: 列+行
           (如: A1, B3, E5)
        """
        st.info(rules)
        
        # 落子输入
        st.subheader("落子")
        pos_input = st.text_input("输入位置 (A1-E5):", "")
        
        col_move1, col_move2 = st.columns(2)
        with col_move1:
            move_clicked = st.button("落子", disabled=st.session_state.game_over)
        
        with col_move2:
            clear_clicked = st.button("清空输入")
        
        # 控制按钮
        st.subheader("控制")
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            slow_clicked = st.button("变慢")
        
        with col_ctrl2:
            fast_clicked = st.button("变快")
        
        col_ctrl3, col_ctrl4 = st.columns(2)
        with col_ctrl3:
            undo_clicked = st.button("悔棋")
        
        with col_ctrl4:
            reset_clicked = st.button("重来")
        
        # 显示当前旋转速度
        st.info(f"当前转速: {st.session_state.rotation_speed:.1f} 度/帧")
        
        # 制作人信息
        st.markdown("---")
        st.markdown("制作人 rotate03 | 版本号 1.0")
    
    # 处理按钮点击事件
    if move_clicked:
        message, color = game.process_move(pos_input)
        st.session_state.message = message
        st.session_state.message_color = color
    
    if clear_clicked:
        # 清空输入框（通过重新运行实现）
        pass
    
    if slow_clicked:
        game.slow_down()
    
    if fast_clicked:
        game.speed_up()
    
    if undo_clicked:
        message, color = game.undo_move()
        st.session_state.message = message
        st.session_state.message_color = color
    
    if reset_clicked:
        game.reset_game()
    
    # 循环更新棋盘旋转和显示
    while True:
        with board_placeholder:
            # 更新旋转
            game.update_rotation()
            # 绘制并显示棋盘
            board_image, buf = game.draw_board()
            st.image(board_image, use_column_width=True)
            buf.close()
        
        with status_placeholder:
            # 显示状态信息
            st.markdown(f"<p style='color:{st.session_state.message_color}; text-align:center; font-size:18px;'>{st.session_state.message}</p>", unsafe_allow_html=True)
        
        # 控制刷新速度
        time.sleep(0.05)
        
        # 如果有按钮点击，退出循环以重新运行
        if move_clicked or clear_clicked or slow_clicked or fast_clicked or undo_clicked or reset_clicked:
            break

if __name__ == "__main__":
    main()
