# **🕹️ Text Annotation Battle**



A gamified web application designed to make large-scale text annotation more engaging and efficient. This platform transforms the annotation of geopolitical risk (GPR)-related content into a collaborative game between two players.

▶️ [Watch Demo](https://gpr-game.onrender.com/static/output_with_subs.mp4)



## **🎯 Project Goal**





To improve data labeling quality and participant motivation by introducing real-time collaboration, game mechanics, and competitive scoring in the annotation process.





## **🌟 Features**





- 👯 **Team-based Real-Time Annotation**: Two players must label the same paragraph sentence-by-sentence and reach agreement to score points.

- 🧠 **Three Attempts per Paragraph**: Encourages thoughtful consensus-building.

- ⏱ **Time-Based Scoring**: Faster agreement means more points.

- 🎁 **Milestone Bonuses**: Extra points for every 100 and 1,000 tasks completed.

- 📊 **Leaderboard**: Live scoreboard showing player rankings.

- 🎮 **Demo Video**: See how it works in action!

  ▶️ [Watch Demo](https://gpr-game.onrender.com/static/output_with_subs.mp4)







## **🛠️ Tech Stack**





- **Backend**: Python, Flask, SQLite, Socket.IO
- **Frontend**: HTML, JavaScript, Bulma CSS
- **Deployment**: Render







## **🚀 Getting Started**



```
git clone https://github.com/zzp-coder/gpr-game.git
cd gpr-game
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.





## **📂 Structure**

- app.py — main server logic with Flask routes and Socket.IO events
- templates/ — HTML templates (login, game, instructions, availability)
- static/ — JavaScript, CSS, and demo video
- data/ — SQLite database storing users, progress, and scores



## **🧪 Demo Accounts**



To try the system locally, you can create two sample users upon first login. You will be automatically paired.