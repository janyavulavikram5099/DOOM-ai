Add-Type -ReferencedAssemblies "System.Speech" -TypeDefinition @"
using System;
using System.IO;
using System.Speech.Recognition;
using System.Threading;

public class TestContinuousListener {
    private SpeechRecognitionEngine engine;
    private ManualResetEvent stopEvent = new ManualResetEvent(false);

    public void Start() {
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

            Choices wake = new Choices(new string[] { "doom", "hey doom", "vikram", "hey vikram" });
            Choices act = new Choices(new string[] { "open", "close" });
            Choices targets = new Choices(new string[] { "whatsapp", "chrome", "settings", "file explorer" });

            GrammarBuilder gb = new GrammarBuilder();
            gb.Append(wake, 0, 1);
            gb.Append(act);
            gb.Append(targets);

            Grammar g = new Grammar(gb);
            engine.LoadGrammar(g);

            engine.SpeechRecognized += (s, e) => {
                Console.WriteLine("RECOGNIZED:" + e.Result.Text + " (Conf: " + e.Result.Confidence + ")");
                Console.Out.Flush();
            };

            engine.SpeechRecognitionRejected += (s, e) => {
                Console.WriteLine("REJECTED:" + (e.Result != null ? e.Result.Text : "<null>"));
                Console.Out.Flush();
            };

            engine.RecognizeAsync(RecognizeMode.Multiple);
            Console.WriteLine("READY:Continuous listener started successfully.");
            Console.Out.Flush();

            // Wait 5 seconds for test
            Thread.Sleep(5000);
            engine.RecognizeAsyncStop();
            Console.WriteLine("STOPPED");
        } catch (Exception ex) {
            Console.WriteLine("ERROR:" + ex.Message);
        }
    }
}
"@

$listener = New-Object TestContinuousListener
$listener.Start()
