# GitHub推送配置指南

## ⚠️ 问题原因
GitHub已经不再支持密码认证，必须使用Personal Access Token (PAT)。

## ✅ 解决方案

### 步骤1：创建GitHub Personal Access Token

1. **访问GitHub设置页面**：
   - 登录GitHub: https://github.com
   - 点击右上角头像 → **Settings** (设置)
   - 左侧菜单最下方 → **Developer settings** (开发者设置)
   - 左侧菜单 → **Personal access tokens** → **Tokens (classic)**

2. **生成新Token**：
   - 点击 **Generate new token** → **Generate new token (classic)**
   - Note (备注): `Backend Tech Knowledge Base Push`
   - Expiration (过期时间): 选择 **No expiration** 或 **90 days**
   
3. **选择权限**（勾选以下选项）：
   - ✅ **repo** (完整的仓库访问权限)
     - repo:status
     - repo_deployment
     - public_repo
     - repo:invite
     - security_events

4. **生成并复制Token**：
   - 点击页面底部 **Generate token**
   - ⚠️ **立即复制Token**（只显示一次！）
   - Token格式类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 步骤2：配置Git使用Token

在终端执行以下命令：

```bash
# 进入项目目录
cd /Users/ymh_sirius/001_File/002code/ai_prompt/cursor_prompt/知识点汇总

# 添加所有文件
git add .

# 提交
git commit -m "初始提交：Java后端技术知识库"

# 推送（会提示输入用户名和密码）
git push -u origin main
```

### 步骤3：输入认证信息

当执行`git push`时，会弹出认证窗口：

```
Username for 'https://github.com': Yanminghao0
Password for 'https://Yanminghao0@github.com': [粘贴你的Token]
```

- **Username**: 你的GitHub用户名 `Yanminghao0`
- **Password**: 粘贴刚才复制的Token（不是GitHub密码！）

### 步骤4：验证推送成功

```bash
# 查看远程仓库状态
git remote -v

# 查看提交日志
git log --oneline

# 访问GitHub查看
https://github.com/Yanminghao0/Backend_Tech_Knowledge_Base
```

---

## 🔧 方法2：使用SSH密钥（更安全，推荐长期使用）

### 生成SSH密钥

```bash
# 生成SSH密钥（使用你的GitHub邮箱）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 按Enter使用默认路径
# 可以设置密码或直接按Enter跳过

# 启动ssh-agent
eval "$(ssh-agent -s)"

# 添加SSH密钥到ssh-agent
ssh-add ~/.ssh/id_ed25519

# 复制公钥到剪贴板
pbcopy < ~/.ssh/id_ed25519.pub
```

### 添加SSH密钥到GitHub

1. 登录GitHub → Settings → SSH and GPG keys
2. 点击 **New SSH key**
3. Title: `MacBook Pro` (任意名称)
4. Key: 粘贴刚才复制的公钥
5. 点击 **Add SSH key**

### 修改远程仓库地址为SSH

```bash
cd /Users/ymh_sirius/001_File/002code/ai_prompt/cursor_prompt/知识点汇总

# 修改远程地址
git remote set-url origin git@github.com:Yanminghao0/Backend_Tech_Knowledge_Base.git

# 验证
git remote -v

# 推送（不需要输入密码）
git push -u origin main
```

---

## 🚨 常见问题

### Q1: Token已过期
重新生成Token，然后清除旧的认证信息：
```bash
# macOS清除keychain中的Git凭证
git credential-osxkeychain erase
host=github.com
protocol=https
[按两次Enter]
```

### Q2: 推送被拒绝（remote rejected）
```bash
# 先拉取远程更改
git pull origin main --allow-unrelated-histories

# 再推送
git push -u origin main
```

### Q3: 仓库不存在
确保在GitHub上已经创建了仓库：
https://github.com/Yanminghao0/Backend_Tech_Knowledge_Base

---

## 📝 快速命令参考

```bash
# 日常推送流程
git add .
git commit -m "更新：描述你的改动"
git push

# 查看状态
git status

# 查看日志
git log --oneline --graph

# 拉取更新
git pull
```

---

**配置完成后，这份文档可以删除！** 🎉

