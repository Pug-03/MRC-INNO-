# How to open the dashboard

Read this if you just want to use the app. No coding knowledge needed.

---

## The easy way: double-click `start.bat`

1. Open File Explorer.
2. Go to the folder `C:\VS_Code_Pug\INNO(Pv)`.
3. Find the file called **`start.bat`** and **double-click it**.
4. Two small black windows will pop up. Do NOT close them — they are the app running.
5. After about 6 seconds, your web browser will open to the dashboard automatically.
6. That's it. Use the app.

### To stop the app

- Close the two black windows (click the X on each). The dashboard tab in your browser can stay open, but it won't receive new data.

### To reopen the app after you closed it

- Just double-click `start.bat` again. Same steps as above.

---

## If the easy way doesn't work — the manual way

You'll open two Command Prompt windows. Each runs one piece of the app. Keep both open.

### Step 1 — Start the backend (the brain)

1. Press the **Windows key**, type **cmd**, press **Enter**. A black window opens.
2. In that black window, type this and press **Enter**:

   ```
   cd C:\VS_Code_Pug\INNO(Pv)\backend
   ```

3. Then type this and press **Enter**:

   ```
   .venv\Scripts\python.exe run.py
   ```

4. You should see lines like `Uvicorn running on http://0.0.0.0:8000`. Good. Leave this window open.

### Step 2 — Start the frontend (the website)

1. Open **another** Command Prompt (Windows key → type **cmd** → Enter).
2. Type this and press **Enter**:

   ```
   cd C:\VS_Code_Pug\INNO(Pv)\frontend
   ```

3. Then type this and press **Enter**:

   ```
   npm run dev
   ```

4. Wait a few seconds. You should see a line like `Local: http://localhost:5175/`. The port number might be 5173, 5174, or 5175 — whichever it says, remember it. Leave this window open too.

### Step 3 — Open the website

1. Open your web browser (Chrome, Edge, Firefox — any of them).
2. In the address bar at the top, type:

   ```
   http://localhost:5175
   ```

   (Use whatever port the frontend window told you in Step 2, if it was different.)

3. Press **Enter**. The dashboard loads.

### To stop the app (manual way)

- Click inside each of the two black windows and press **Ctrl+C**, or just close them with the X.

### To reopen after closing

- Repeat Step 1, Step 2, Step 3. Same commands, same order.

---

## The Pause button

There is now a **Pause** button in the top-right of the camera panel. Click it to stop counting caps temporarily — the camera keeps showing the video but nothing gets added to the totals. Click **Resume** to start counting again. Use this when you take a break or swap caps, so you don't need to restart the whole app.

---

## Troubleshooting

- **Browser says "can't connect" or "site can't be reached"**: the servers aren't running yet. Wait 5–10 seconds after starting and refresh. If still not working, check that both black windows are open.
- **Wrong port number**: look at the frontend black window — it will say `Local: http://localhost:XXXX/` — use that exact address.
- **The black window closes immediately**: something is broken with the install. Open a Command Prompt manually and run the commands (Step 1 / Step 2 above) one at a time so you can read the error message.
