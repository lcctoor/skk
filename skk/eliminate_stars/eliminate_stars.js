class GravityGame extends HTMLElement {
    constructor() {
        super();
        // 创建影子DOM
        this.attachShadow({ mode: 'open' });

        // 组件状态
        this.score = 0;
        this.gameActive = false;
        this.playerX = 0;
        this.playerY = 0;
        this.collectibles = [];
        this.playerSpeed = 3;
        this.animationFrameId = null;

        // 定时生成相关配置
        this.spawnInterval = 1500; // 生成间隔（毫秒）
        this.start_count = 20  // 初始星星数量
        this.maxCollectibles = 50;  // 最大星星数量
        this.spawnTimer = null;    // 定时器ID

        // 新增：连杀计数相关
        this.killStreak = 0;  // 连杀计数器

        // 浏览器
        this.gravityX = 0;
        this.gravityY = 0;

        // 初始化组件
        this.init();
    }

    // 初始化组件结构和样式
    init() {
        // 组件HTML结构（保留原有CSS）
        this.shadowRoot.innerHTML = `
                    <style>
                        :host {
                            display: block;
                            width: 100vw;
                            height: 100vh;
                            overflow: hidden;
                        }
                        #game-container {
                            position: relative;
                            width: 100%;
                            height: 100%;
                            background: #0f172a;
                        }
                        #player {
                            position: absolute;
                            width: 40px;
                            height: 40px;
                            border-radius: 50%;
                            background: linear-gradient(135deg, #3b82f6, #60a5fa);
                            box-shadow: 0 0 15px rgba(59, 130, 246, 0.8);
                            z-index: 2;
                        }
                        .collectible {
                            position: absolute;
                            width: 30px;
                            height: 30px;
                            background: linear-gradient(135deg, #f59e0b, #fbbf24);
                            border-radius: 50%;
                            box-shadow: 0 0 10px rgba(245, 158, 11, 0.8);
                            z-index: 1;
                        }
                        #score {
                            position: fixed;
                            top: 40px;
                            left: 20px;
                            color: white;
                            font-family: Arial, sans-serif;
                            font-size: 24px;
                            font-weight: bold;
                            z-index: 10;
                        }
                        #controls {
                            position: fixed;
                            bottom: 20px;
                            left: 50%;
                            transform: translateX(-50%);
                            z-index: 10;
                            display: grid;
                            grid-template-columns: 6rem 6rem;
                            align-content: center;
                        }
                        button {
                            padding: 10px 20px;
                            background: #3b83f673;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            font-size: 16px;
                            cursor: pointer;
                            margin: 0 5px;
                        }
                        button:hover {
                            background: #3b83f673;
                        }
                        /* 全消除特效样式 */
                        .clear-effect {
                            position: absolute;
                            width: 100px;
                            height: 100px;
                            border-radius: 50%;
                            background: rgba(255, 215, 0, 0.6);
                            transform: translate(-50%, -50%) scale(0);
                            z-index: 5;
                            pointer-events: none;
                        }
                        .clear-effect.animate {
                            animation: pulse 1s ease-out forwards;
                        }
                        @keyframes pulse {
                            0% { transform: translate(-50%, -50%) scale(0); opacity: 1; }
                            50% { transform: translate(-50%, -50%) scale(3); opacity: 0.8; }
                            100% { transform: translate(-50%, -50%) scale(5); opacity: 0; }
                        }
                        .clear-text {
                            position: absolute;
                            color: white;
                            font-family: Arial, sans-serif;
                            font-size: 64px;
                            font-weight: bold;
                            text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
                            transform: translate(-50%, -50%) scale(0);
                            z-index: 6;
                            pointer-events: none;
                        }
                        .clear-text.animate {
                            animation: pop 1s ease-out forwards;
                        }
                        @keyframes pop {
                            0% { transform: translate(-50%, -50%) scale(0); opacity: 1; }
                            50% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
                            70% { transform: translate(-50%, -50%) scale(0.9); opacity: 1; }
                            100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
                        }
                    </style>
                    
                    <div id="game-container">
                        <div id="player"></div>
                        <div id="score">分数: 0</div>
                        <div id="controls">
                            <button id="start-btn">开始游戏</button>
                            <button id="reset-btn">重置游戏</button>
                        </div>
                    </div>
                `;

        // 获取组件内部元素
        this.gameContainer = this.shadowRoot.getElementById('game-container');
        this.player = this.shadowRoot.getElementById('player');
        this.scoreDisplay = this.shadowRoot.getElementById('score');
        this.startBtn = this.shadowRoot.getElementById('start-btn');
        this.resetBtn = this.shadowRoot.getElementById('reset-btn');

        // 绑定事件
        this.bindEvents();

        // 初始化游戏
        this.initGame();
    }

    // 绑定事件监听
    bindEvents() {
        this.startBtn.addEventListener('click', () => this.toggleGame());
        this.resetBtn.addEventListener('click', () => this.resetGame());
        window.addEventListener('resize', () => this.handleResize());

        // 浏览器
        window.addEventListener('deviceorientation', (event) => {
            this.gravityX = event.gamma;
            this.gravityY = event.beta;
        })
    }

    // 初始化游戏状态
    initGame() {
        this.resetPlayerPosition();
        this.clearCollectibles();
        // 初始化时生成初始数量星星
        for (let i = 0; i < this.start_count; i++) {
            this.createSingleCollectible();
        }
        this.score = 0;
        this.killStreak = 0;  // 重置连杀计数
        this.updateScoreDisplay();
    }

    // 重置玩家位置到中心
    resetPlayerPosition() {
        this.playerX = this.gameContainer.clientWidth / 2 - this.player.clientWidth / 2;
        this.playerY = this.gameContainer.clientHeight / 2 - this.player.clientHeight / 2;
        this.updatePlayerPosition();
    }

    // 更新玩家位置
    updatePlayerPosition() {
        // 边界检查
        if (this.playerX < 0) this.playerX = 0;
        if (this.playerX > this.gameContainer.clientWidth - this.player.clientWidth) {
            this.playerX = this.gameContainer.clientWidth - this.player.clientWidth;
        }
        if (this.playerY < 0) this.playerY = 0;
        if (this.playerY > this.gameContainer.clientHeight - this.player.clientHeight) {
            this.playerY = this.gameContainer.clientHeight - this.player.clientHeight;
        }

        this.player.style.left = `${this.playerX}px`;
        this.player.style.top = `${this.playerY}px`;
    }

    // 生成单个星星
    createSingleCollectible() {
        const collectible = document.createElement('div');
        collectible.className = 'collectible';
        this.gameContainer.appendChild(collectible);

        // 随机位置（避开边缘）
        const x = Math.random() * (this.gameContainer.clientWidth - 60) + 30;
        const y = Math.random() * (this.gameContainer.clientHeight - 60) + 30;

        collectible.style.left = `${x}px`;
        collectible.style.top = `${y}px`;

        this.collectibles.push({
            element: collectible,
            x: x,
            y: y
        });

        // 新增：如果生成的是第2颗及以上星星，且游戏活跃，重置连杀计数
        if (this.collectibles.length >= 2 && this.gameActive) {
            this.killStreak = 0;
        }
    }

    // 清除所有收集物
    clearCollectibles() {
        this.collectibles.forEach(item => item.element.remove());
        this.collectibles = [];
    }

    // 更新分数显示
    updateScoreDisplay() {
        this.scoreDisplay.textContent = `分数: ${this.score}`;
    }

    // 显示连杀特效
    showClearEffect() {
        // 创建特效元素
        const effect = document.createElement('div');
        effect.className = 'clear-effect';
        effect.style.left = `${this.gameContainer.clientWidth / 2}px`;
        effect.style.top = `${this.gameContainer.clientHeight / 2}px`;

        // 创建文字元素（显示连杀数）
        const text = document.createElement('div');
        text.className = 'clear-text';
        text.textContent = `${this.killStreak}杀`;  // 显示"1杀"、"2杀"等
        text.style.left = `${this.gameContainer.clientWidth / 2}px`;
        text.style.top = `${this.gameContainer.clientHeight / 2}px`;

        // 添加到游戏容器
        this.gameContainer.appendChild(effect);
        this.gameContainer.appendChild(text);

        // 触发动画
        setTimeout(() => {
            effect.classList.add('animate');
            text.classList.add('animate');
        }, 10);

        // 动画结束后移除元素
        setTimeout(() => {
            effect.remove();
            text.remove();
        }, 1000);
    }

    // 检测碰撞
    checkCollisions() {
        let allCleared = false;

        this.collectibles.forEach((collectible, index) => {
            const playerRect = this.player.getBoundingClientRect();
            const collectibleRect = collectible.element.getBoundingClientRect();

            if (
                playerRect.left < collectibleRect.right &&
                playerRect.right > collectibleRect.left &&
                playerRect.top < collectibleRect.bottom &&
                playerRect.bottom > collectibleRect.top
            ) {
                // 移除收集物
                collectible.element.remove();
                this.collectibles.splice(index, 1);

                // 增加分数
                this.score++;
                this.updateScoreDisplay();

                // 检查是否所有星星都被消除
                if (this.collectibles.length === 0) {
                    allCleared = true;
                }
            }
        });

        // 如果所有星星都被消除，更新连杀计数并显示特效
        if (allCleared) {
            this.killStreak++;  // 连杀计数+1
            this.showClearEffect();
        }
    }

    // 定时生成星星
    startSpawning() {
        // 清除可能存在的旧定时器
        if (this.spawnTimer) clearInterval(this.spawnTimer);

        // 定时生成星星
        this.spawnTimer = setInterval(() => {
            // 星星数量未达上限且游戏活跃时才生成
            if (this.collectibles.length < this.maxCollectibles && this.gameActive) {
                this.createSingleCollectible();
            }
        }, this.spawnInterval);
    }

    // 停止生成星星
    stopSpawning() {
        if (this.spawnTimer) {
            clearInterval(this.spawnTimer);
            this.spawnTimer = null;
        }
    }

    // 浏览器
    getGravityData() {
        return {
            x: this.gravityX * 0.16,
            y: this.gravityY * 0.16,
        };
    }

    // 游戏主循环
    gameLoop() {
        if (!this.gameActive) return;

        // 获取重力数据
        const gravity = this.getGravityData();

        // 根据重力数据移动玩家
        this.playerX += gravity.x * this.playerSpeed;
        this.playerY += gravity.y * this.playerSpeed;

        // 更新玩家位置
        this.updatePlayerPosition();

        // 检测碰撞
        this.checkCollisions();

        // 继续游戏循环
        this.animationFrameId = requestAnimationFrame(() => this.gameLoop());
    }

    // 切换游戏状态（开始/暂停）
    toggleGame() {
        if (!this.gameActive) {
            this.gameActive = true;
            this.gameLoop();
            this.startSpawning(); // 开始定时生成
            this.startBtn.textContent = "暂停游戏";
        } else {
            this.gameActive = false;
            cancelAnimationFrame(this.animationFrameId);
            this.stopSpawning(); // 暂停生成
            this.startBtn.textContent = "继续游戏";
        }
    }

    // 重置游戏
    resetGame() {
        this.gameActive = false;
        cancelAnimationFrame(this.animationFrameId);
        this.stopSpawning(); // 停止生成
        this.startBtn.textContent = "开始游戏";
        this.initGame();
    }

    // 处理窗口大小变化
    handleResize() {
        if (!this.gameActive) {
            this.resetPlayerPosition();
        }
    }

    // 组件销毁时清理
    disconnectedCallback() {
        this.gameActive = false;
        cancelAnimationFrame(this.animationFrameId);
        this.stopSpawning(); // 清除定时器
        window.removeEventListener('resize', () => this.handleResize());
    }
}

// 注册自定义元素
customElements.define('gravity-game', GravityGame);
