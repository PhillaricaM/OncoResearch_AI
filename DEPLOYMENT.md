# Free public portfolio demo

Use Streamlit Community Cloud for the interface and a Render Free web service for FastAPI. These steps assume this repository's root contains `backend/`, `frontend/`, and `render.yaml`.

## 1. Upload the prepared files

In VS Code Source Control, review and stage the changes, commit them, then Sync Changes. Confirm the new files appear on GitHub. Never upload `.venv`, `.env`, or `.streamlit/secrets.toml`.

## 2. Deploy the backend on Render

1. Sign in at https://dashboard.render.com/ using GitHub.
2. Choose New → Web Service, and connect `PhillaricaM/OncoResearch_AI`.
3. Select the branch containing your latest changes. Leave Root Directory blank.
4. Choose the Python runtime.
5. Build command: `pip install -r backend/requirements.txt && python scripts/build_oncocompute.py` (requires g++ on the build host).
6. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
7. Select the **Free** instance type. Do not select a paid plan or add a database.
8. Create the service and wait for deployment to complete.
9. Copy the actual HTTPS service URL Render assigns. Open that URL followed by `/health`; verify `status` is `ok`.

Alternatively, `render.yaml` defines the same free backend service for Render's Blueprint workflow. Use either method, not both.

The backend does not need a database or ChEMBL API key. Its source host is fixed in the code. Requests come from the Streamlit Python server, so browser CORS configuration is not needed for this architecture.

## 3. Deploy the frontend on Streamlit Community Cloud

1. Sign in at https://share.streamlit.io/ with GitHub.
2. Choose Create app and select `PhillaricaM/OncoResearch_AI`.
3. Choose the same branch containing your updates.
4. Set Main file path to `frontend/app.py`.
5. Open Advanced settings. In Secrets, enter the following, replacing the example with your actual Render service URL:

```toml
ONCORESEARCH_API_URL = "https://YOUR-ACTUAL-SERVICE.onrender.com"
```

6. Deploy the app. Community Cloud installs the root `requirements.txt`; the Windows development lock file is not used for this Linux deployment.
7. Ensure app sharing is public and copy the assigned `streamlit.app` URL.

The top-level setting becomes an environment variable, which the app already reads. This URL is configuration, not a password. Never use `localhost` for the hosted backend address.

## 4. Verify as a visitor

1. Stop both local servers on your computer.
2. Open the public Streamlit URL in a private/incognito browser window.
3. Search for aspirin and confirm a results table appears.
4. Download the CSV and JSON research record.
5. Enable each Tableau dashboard and check it loads. Test the direct Tableau links too.
6. Confirm the page can be viewed without signing into your accounts.

If the first search fails, check Render's service logs, confirm `/health` works, and retry after the backend wakes. Check the URL configured in Streamlit Secrets and reboot the app if needed. Tableau browser/cookie restrictions can affect embedded views; direct links remain available.

## 5. Share with employers

Add the verified public app URL near the top of README.md under **Live demo**. Include a screenshot, link to the GitHub repository, and note that the free backend may take about a minute to wake. Add the live URL to the repository's About → Website field.

Free services have usage limits, can sleep, and do not provide an always-on availability guarantee. Review the providers' current free limits before deploying. No external deployment is performed by adding these files.

Official documentation:

- https://docs.streamlit.io/deploy/streamlit-community-cloud
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://render.com/docs/free
