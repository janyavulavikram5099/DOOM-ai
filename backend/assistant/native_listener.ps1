# ==============================================================================
# DOOM AI - Native Windows Offline Speech Recognition Engine
# Powered by in-process compiled C# with asynchronous continuous streaming.
# Works 100% OFFLINE with zero internet, zero cloud servers, zero pip packages.
# Exclusively optimized for Open and Close commands, application control, and system hardware.
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Speech -ErrorAction Stop

# Compile High-Performance Continuous Native Listener
Add-Type -ReferencedAssemblies "System.Speech" -TypeDefinition @"
using System;
using System.IO;
using System.Collections.Generic;
using System.Speech.Recognition;
using System.Threading;

public class DoomOfflineContinuousListener : IDisposable {
    private SpeechRecognitionEngine engine;
    private ManualResetEvent exitEvent = new ManualResetEvent(false);
    private bool isDisposed = false;
    public volatile bool IsPaused = false;

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

            // Far-field acoustic sensitivity configuration
            engine.InitialSilenceTimeout = TimeSpan.FromSeconds(10);
            engine.BabbleTimeout = TimeSpan.FromSeconds(10);
            engine.EndSilenceTimeout = TimeSpan.FromMilliseconds(450);
            engine.EndSilenceTimeoutAmbiguous = TimeSpan.FromMilliseconds(450);

            // 1. Wake Words (Focused on actual wake phrases)
            Choices wakeWords = new Choices(new string[] {
                "hey doom", "doom", "hi doom", "hello doom", "ok doom", "okay doom",
                "hey vikram", "vikram", "hi vikram", "hello vikram", "ok vikram", "okay vikram",
                "doom ai"
            });

            // 2. Open Verbs & Modifiers
            Choices openVerbs = new Choices(new string[] {
                "open", "launch", "start", "run", "show", "open up", "bring up"
            });
            Choices articles = new Choices(new string[] { "the", "my", "the app", "application" });
            Choices suffixes = new Choices(new string[] { "please", "now", "app", "application", "window" });

            // Comprehensive target applications list
            HashSet<string> appSet = new HashSet<string>(StringComparer.OrdinalIgnoreCase) {
                "whatsapp", "chrome", "google chrome", "browser", "the browser",
                "edge", "microsoft edge", "file explorer", "file explore", "files", "my files",
                "explorer", "folder", "folders", "downloads", "documents", "this pc", "my computer",
                "settings", "setting", "windows settings", "pc settings", "system settings", "laptop settings",
                "display settings", "sound settings", "audio settings", "wifi settings", "bluetooth settings",
                "notepad", "vs code", "vscode", "code", "calculator", "calc",
                "terminal", "cmd", "command prompt", "powershell", "paint", "camera", "word", "excel", "powerpoint",
                "task manager", "vantage", "lenovo vantage", "youtube", "gmail", "email",
                "discord", "spotify", "telegram", "steam", "vlc", "vlc player", "roblox", "epic games", "zoom", "teams",
                "netflix", "movies", "clock", "alarms", "photos", "store", "microsoft store"
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

            // Open Grammar: [wake]? + [openVerb] + [article]? + [target] + [suffix]?
            GrammarBuilder openGb = new GrammarBuilder();
            openGb.Append(wakeWords, 0, 1);
            openGb.Append(openVerbs);
            openGb.Append(articles, 0, 1);
            openGb.Append(targetChoices);
            openGb.Append(suffixes, 0, 1);

            Grammar openGrammar = new Grammar(openGb);
            openGrammar.Priority = 127;
            engine.LoadGrammar(openGrammar);

            // 3. Close Grammar: Dedicated standalone, active window, tabs, all, and named apps
            List<string> closeList = new List<string> {
                // Standalone & Active Window
                "close", "close it", "close this", "close that",
                "close window", "close the window", "close this window", "close active window", "close current window",
                "close app", "close the app", "close this app", "close active app", "close current app",
                "close application", "close the application", "close this application", "close program",
                "quit", "quit it", "quit this", "quit app", "quit window", "quit the app", "quit the window",
                "exit", "exit it", "exit this", "exit app", "exit window", "exit the app", "exit the window",
                "stop it", "terminate app", "kill app", "kill this",

                // Tab Close
                "close tab", "close the tab", "close this tab", "close current tab", "close active tab",
                "close browser tab", "close window tab",

                // Close All Apps / Windows
                "close all", "close all apps", "close all applications", "close all windows", "close all programs",
                "close all tabs", "close apps", "close everything", "quit all", "exit all", "close all app",

                // Phonetic / Acoustic Close Synonyms
                "clothes settings", "closed settings", "clothes window", "clothes app", "clothes",
                "close sitting", "close sittings", "closed setting", "clothes setting",
                "closed window", "closed tab", "closed all"
            };

            // Add target-specific close: "close <app>" and reverse "<app> close"
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

            // 4. System & Hardware Controls (100% Offline)
            Choices sysCmds = new Choices(new string[] {
                // Brightness
                "increase brightness", "decrease brightness", "brightness up", "brightness down",
                "max brightness", "min brightness", "maximum brightness", "minimum brightness",
                "brighter", "dimmer", "check brightness", "brightness status",
                "set brightness to 50 percent", "set brightness to 100 percent",

                // Volume & Audio
                "volume up", "volume down", "increase volume", "decrease volume",
                "volume max", "max volume", "maximum volume", "volume min", "min volume", "minimum volume",
                "mute", "unmute", "mute audio", "unmute audio", "mute sound", "unmute sound",
                "louder", "quieter", "set volume to max",

                // Workstation Security
                "lock laptop", "lock my laptop", "lock pc", "lock computer", "lock screen", "lock",
                "unlock laptop", "unlock my laptop", "unlock", "unlock with 8055", "8055",
                "take screenshot", "take a screenshot", "capture screen", "screenshot",
                "sleep laptop", "sleep pc", "put computer to sleep", "sleep",
                "restart laptop", "restart pc", "restart",
                "shutdown laptop", "shut down laptop", "shutdown pc", "shutdown computer",

                // Telemetry & Time (100% Offline)
                "system status", "battery percentage", "battery status", "what is charging",
                "charging percentage", "what time is it", "what is the time", "time", "current time",
                "what is the date today", "what date is today", "what is today's date", "what is today date",
                "what's the date today", "whats the date today", "tell me the date today", "tell me the date",
                "tell me today's date", "today's date", "todays date", "date today", "what date is it",
                "what is the date", "what is date today", "date", "current date", "today date",

                // Wi-Fi Controls (100% Offline)
                "turn on wifi", "turn one wifi", "turn 1 wifi", "turn on the wifi", "turn one the wifi",
                "turn on wi-fi", "turn one wi-fi", "turn on the wi-fi", "turn one the wi-fi",
                "wifi on", "wifi one", "wi-fi on", "wi-fi one", "turn wifi on", "turn wifi one", "turn wi-fi on", "turn wi-fi one",
                "enable wifi", "enable wi-fi", "switch on wifi", "switch one wifi", "switch on wi-fi", "switch one wi-fi",
                "turn off wifi", "turn off the wifi", "turn off wi-fi", "turn off the wi-fi", "turn of wifi", "turn of wi-fi",
                "wifi off", "wi-fi off", "turn wifi off", "turn wi-fi off", "disable wifi", "disable wi-fi",
                "switch off wifi", "switch off wi-fi", "disconnect wifi", "stop wifi", "wifi status", "check wifi",

                // Bluetooth Controls (100% Offline)
                "turn on bluetooth", "turn one bluetooth", "turn 1 bluetooth", "turn on the bluetooth", "turn one the bluetooth",
                "bluetooth on", "bluetooth one", "turn bluetooth on", "turn bluetooth one",
                "enable bluetooth", "switch on bluetooth", "switch one bluetooth", "switch on the bluetooth", "switch one the bluetooth",
                "turn off bluetooth", "turn off the bluetooth", "turn of bluetooth", "turn of the bluetooth",
                "bluetooth off", "turn bluetooth off", "disable bluetooth", "switch off bluetooth", "switch off the bluetooth",
                "bluetooth status", "check bluetooth"
            });

            GrammarBuilder sysGb = new GrammarBuilder();
            sysGb.Append(wakeWords, 0, 1);
            sysGb.Append(sysCmds);
            Grammar sysGrammar = new Grammar(sysGb);
            sysGrammar.Priority = 127;
            engine.LoadGrammar(sysGrammar);

            // 5. Standalone Wake Words Grammar
            GrammarBuilder wakeGb = new GrammarBuilder(wakeWords);
            Grammar wakeGrammar = new Grammar(wakeGb);
            wakeGrammar.Priority = 127;
            engine.LoadGrammar(wakeGrammar);

            // Stdin command listener (handles PAUSE, RESUME, STOP from Python daemon)
            Thread stdinThread = new Thread(() => {
                try {
                    string line;
                    while (!isDisposed && (line = Console.ReadLine()) != null) {
                        string cmd = line.Trim().ToUpperInvariant();
                        if (cmd == "PAUSE") {
                            IsPaused = true;
                        } else if (cmd == "RESUME") {
                            IsPaused = false;
                        } else if (cmd == "STOP" || cmd == "EXIT") {
                            Stop();
                            break;
                        }
                    }
                } catch {}
            });
            stdinThread.IsBackground = true;
            stdinThread.Start();

            // Real-Time Event Handlers
            engine.SpeechRecognized += (s, e) => {
                if (IsPaused) return;
                if (e.Result != null && !string.IsNullOrWhiteSpace(e.Result.Text) && e.Result.Confidence >= 0.65f) {
                    Console.WriteLine("RECOGNIZED:" + e.Result.Text);
                    Console.Out.Flush();
                }
            };

            engine.RecognizeCompleted += (s, e) => {
                if (!isDisposed) {
                    try {
                        engine.RecognizeAsync(RecognizeMode.Multiple);
                    } catch {}
                }
            };

            // Start continuous asynchronous listening
            engine.RecognizeAsync(RecognizeMode.Multiple);

            Console.WriteLine("READY:DOOM Native Continuous Speech Recognizer Initialized (Offline Open/Close Engine Active).");
            Console.Out.Flush();

            exitEvent.WaitOne();
        } catch (Exception ex) {
            Console.WriteLine("ERROR:" + ex.Message);
            Console.Out.Flush();
        }
    }

    public void Stop() {
        isDisposed = true;
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

# Load Extra App Targets from Catalog
$targetApps = @()
try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $catalogPath = Join-Path (Split-Path -Parent $scriptDir) "execution\installed_apps.json"
    if (Test-Path $catalogPath) {
        $json = Get-Content -Path $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($json -ne $null) {
            foreach ($prop in $json.psobject.Properties) {
                $name = $prop.Name
                if ($name -and $name.Length -ge 2 -and $name.Length -le 35) {
                    $targetApps += $name.ToLower().Trim()
                }
            }
        }
    }
} catch {}

# Supervisor Loop to ensure auto-recovery across device resets
while ($true) {
    $listener = $null
    try {
        $listener = New-Object DoomOfflineContinuousListener
        $listener.Start([string[]]$targetApps)
    } catch {
        [Console]::WriteLine("NOTICE: Listener exception, restarting in 1s: " + $_.Exception.Message)
        [Console]::Out.Flush()
    } finally {
        if ($listener -ne $null) {
            try { $listener.Dispose() } catch {}
        }
    }
    Start-Sleep -Milliseconds 1200
}
