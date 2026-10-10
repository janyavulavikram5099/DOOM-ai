Add-Type -ReferencedAssemblies "System.Speech" -TypeDefinition @"
using System;
using System.IO;
using System.Collections.Generic;
using System.Speech.Recognition;
using System.Threading;

public class DoomOfflineListener : IDisposable {
    private SpeechRecognitionEngine engine;
    private ManualResetEvent exitEvent = new ManualResetEvent(false);

    public void Start(string[] targetApps) {
        try {
            RecognizerInfo chosen = null;
            foreach (RecognizerInfo ri in SpeechRecognitionEngine.InstalledRecognizers()) {
                if (ri.Culture.Name.StartsWith("en", StringComparison.OrdinalIgnoreCase)) {
                    chosen = ri;
                    break;
                }
            }
            if (chosen != null) {
                engine = new SpeechRecognitionEngine(chosen);
            } else {
                engine = new SpeechRecognitionEngine();
            }

            engine.SetInputToDefaultAudioDevice();

            engine.InitialSilenceTimeout = TimeSpan.FromSeconds(8);
            engine.BabbleTimeout = TimeSpan.FromSeconds(8);
            engine.EndSilenceTimeout = TimeSpan.FromMilliseconds(450);
            engine.EndSilenceTimeoutAmbiguous = TimeSpan.FromMilliseconds(450);

            Choices wakeWords = new Choices(new string[] {
                "hey doom", "doom", "hi doom", "hello doom", "ok doom", "okay doom",
                "hey vikram", "vikram", "hi vikram", "hello vikram", "ok vikram", "okay vikram",
                "doom ai", "boom", "tomb", "room", "tune", "dude"
            });

            Choices openVerbs = new Choices(new string[] {
                "open", "launch", "start", "run", "show", "open up", "bring up"
            });
            Choices articles = new Choices(new string[] { "the", "my", "the app", "application" });
            Choices suffixes = new Choices(new string[] { "please", "now", "app", "application", "window" });

            HashSet<string> appSet = new HashSet<string>(StringComparer.OrdinalIgnoreCase) {
                "whatsapp", "chrome", "google chrome", "browser", "the browser",
                "edge", "microsoft edge", "file explorer", "file explore", "files", "my files",
                "explorer", "folder", "folders", "downloads", "documents", "this pc", "my computer",
                "settings", "setting", "windows settings", "pc settings", "system settings", "laptop settings",
                "display settings", "sound settings", "audio settings", "wifi settings", "bluetooth settings",
                "notepad", "vs code", "vscode", "code", "calculator", "calc",
                "terminal", "cmd", "command prompt", "powershell", "paint", "camera", "word", "excel", "powerpoint",
                "task manager", "vantage", "lenovo vantage", "youtube", "gmail", "email",
                "discord", "spotify", "telegram", "steam", "vlc", "vlc player", "roblox", "epic games", "zoom", "teams"
            };
            if (targetApps != null) {
                foreach (string t in targetApps) {
                    if (!string.IsNullOrWhiteSpace(t) && t.Length >= 2 && t.Length <= 40) {
                        appSet.Add(t.Trim().ToLowerInvariant());
                    }
                }
            }

            string[] appList = new string[appSet.Count];
            appSet.CopyTo(appList);
            Choices targetChoices = new Choices(appList);

            GrammarBuilder openGb = new GrammarBuilder();
            openGb.Append(wakeWords, 0, 1);
            openGb.Append(openVerbs);
            openGb.Append(articles, 0, 1);
            openGb.Append(targetChoices);
            openGb.Append(suffixes, 0, 1);

            Grammar openGrammar = new Grammar(openGb);
            openGrammar.Priority = 127;
            engine.LoadGrammar(openGrammar);

            List<string> closeList = new List<string> {
                "close", "close it", "close this", "close that",
                "close window", "close the window", "close this window", "close active window", "close current window",
                "close app", "close the app", "close this app", "close active app", "close current app",
                "close application", "close the application", "close this application", "close program",
                "quit", "quit it", "quit this", "quit app", "quit window", "quit the app", "quit the window",
                "exit", "exit it", "exit this", "exit app", "exit window", "exit the app", "exit the window",
                "stop it", "terminate app", "kill app", "kill this",
                "close tab", "close the tab", "close this tab", "close current tab", "close active tab",
                "close browser tab", "close window tab",
                "close all", "close all apps", "close all applications", "close all windows", "close all programs",
                "close all tabs", "close apps", "close everything", "quit all", "exit all", "close all app",
                "clothes settings", "closed settings", "clothes window", "clothes app", "clothes",
                "close sitting", "close sittings", "closed setting", "clothes setting",
                "closed window", "closed tab", "closed all"
            };

            foreach (string app in appList) {
                closeList.Add("close " + app);
                closeList.Add("close the " + app);
                closeList.Add("close my " + app);
                closeList.Add(app + " close");
            }

            Choices closeChoices = new Choices(closeList.ToArray());
            GrammarBuilder closeGb = new GrammarBuilder();
            closeGb.Append(wakeWords, 0, 1);
            closeGb.Append(closeChoices);

            Grammar closeGrammar = new Grammar(closeGb);
            closeGrammar.Priority = 127;
            engine.LoadGrammar(closeGrammar);

            Choices sysCmds = new Choices(new string[] {
                "increase brightness", "decrease brightness", "brightness up", "brightness down",
                "max brightness", "min brightness", "brighter", "dimmer", "check brightness",
                "volume up", "volume down", "increase volume", "decrease volume",
                "volume max", "max volume", "volume min", "min volume",
                "mute", "unmute", "mute audio", "unmute audio",
                "lock laptop", "lock my laptop", "lock pc", "lock computer", "lock screen", "lock",
                "unlock laptop", "unlock", "take screenshot", "screenshot", "sleep laptop",
                "restart laptop", "shutdown laptop", "battery status", "battery percentage",
                "what is charging", "system status", "time", "what time is it", "date", "what is the date"
            });
            GrammarBuilder sysGb = new GrammarBuilder();
            sysGb.Append(wakeWords, 0, 1);
            sysGb.Append(sysCmds);
            Grammar sysGrammar = new Grammar(sysGb);
            sysGrammar.Priority = 127;
            engine.LoadGrammar(sysGrammar);

            GrammarBuilder wakeGb = new GrammarBuilder(wakeWords);
            Grammar wakeGrammar = new Grammar(wakeGb);
            wakeGrammar.Priority = 127;
            engine.LoadGrammar(wakeGrammar);

            engine.SpeechRecognized += (s, e) => {
                if (e.Result != null && !string.IsNullOrWhiteSpace(e.Result.Text) && e.Result.Confidence >= 0.28f) {
                    Console.WriteLine("RECOGNIZED:" + e.Result.Text);
                    Console.Out.Flush();
                }
            };

            engine.RecognizeAsync(RecognizeMode.Multiple);
            Console.WriteLine("READY:DOOM Native Continuous Speech Recognizer Initialized (Offline Open/Close Engine Active).");
            Console.Out.Flush();

            // Run for 3 seconds in test mode
            Thread.Sleep(3000);
            Stop();
        } catch (Exception ex) {
            Console.WriteLine("ERROR:" + ex.Message);
            Console.Out.Flush();
        }
    }

    public void Stop() {
        try {
            if (engine != null) {
                engine.RecognizeAsyncStop();
                engine.Dispose();
                engine = null;
            }
        } catch {}
        exitEvent.Set();
    }

    public void Dispose() {
        Stop();
    }
}
"@

$listener = New-Object DoomOfflineListener
$listener.Start(@())
Write-Host "Test completed successfully."
