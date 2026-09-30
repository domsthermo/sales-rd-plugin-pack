# Install ProspectPro

## ChatGPT desktop

1. Extract the ZIP and keep the top-level folder named `prospectpro`.
2. Place that folder at:
   - macOS or Linux: `~/plugins/prospectpro`
   - Windows: `%USERPROFILE%\plugins\prospectpro`
3. Add ProspectPro to the personal marketplace file:
   - macOS or Linux: `~/.agents/plugins/marketplace.json`
   - Windows: `%USERPROFILE%\.agents\plugins\marketplace.json`

   If the marketplace file does not exist, create it with:

   ```json
   {
     "name": "personal",
     "interface": {"displayName": "Personal"},
     "plugins": [
       {
         "name": "prospectpro",
         "source": {"source": "local", "path": "./plugins/prospectpro"},
         "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
         "category": "Productivity"
       }
     ]
   }
   ```

   If the file already exists, preserve its current entries and append only the ProspectPro object inside `plugins`.
4. Restart the ChatGPT desktop app.
5. Open the Plugins Directory, select the `Personal` source, open ProspectPro, and choose **Install**.
6. Start a new task and ask ProspectPro to analyze a named customer and an uploaded purchase-history workbook.

## ChatGPT web

The portable plugin can be made available on the web after publication; a local folder is not directly available to ordinary web chats.

- For private organizational use, a ChatGPT workspace administrator can open **Plugins → Personal**, open ProspectPro's menu, select **Publish**, and choose the permitted workspace roles.
- For public distribution, submit the portable plugin through the universal Plugins Directory review process.

Each user must separately have permission to use plugins, web research, file uploads, and Outlook when Outlook evidence or writing-style personalization is desired. ProspectPro does not bundle Outlook credentials or send email.
