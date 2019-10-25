using System;
using System.IO;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Drawing;
using System.Linq;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using Microsoft.Kinect;
using Sacknet.KinectFacialRecognition;

namespace Sacknet.KinectFacialRecognitionScanner
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        private KinectFacialRecognitionEngine engine;
        private ObservableCollection<TargetFace> targetFaces = new ObservableCollection<TargetFace>();
        private ObservableCollection<OutputUser> outputUsers = new ObservableCollection<OutputUser>();

        /// <summary>
        /// Initializes a new instance of the MainWindow class
        /// </summary>
        public MainWindow()
        {
            KinectSensor kinectSensor = null;

            // loop through all the Kinects attached to this PC, and start the first that is connected without an error.
            foreach (KinectSensor kinect in KinectSensor.KinectSensors)
            {
                if (kinect.Status == KinectStatus.Connected)
                {
                    kinectSensor = kinect;
                    break;
                }
            }

            if (kinectSensor == null)
            {
                MessageBox.Show("No Kinect found...");
                Application.Current.Shutdown();
                return;
            }

            kinectSensor.SkeletonStream.Enable();
            kinectSensor.ColorStream.Enable(ColorImageFormat.RgbResolution640x480Fps30);
            kinectSensor.DepthStream.Enable(DepthImageFormat.Resolution640x480Fps30);
            kinectSensor.Start();

            AllFramesReadyFrameSource frameSource = new AllFramesReadyFrameSource(kinectSensor);
            this.engine = new KinectFacialRecognitionEngine(kinectSensor, frameSource);
            this.engine.RecognitionComplete += this.Engine_RecognitionComplete;

            this.InitializeComponent();

            while ("PiTFT-lakechamplain-temp" != Directory.GetCurrentDirectory().Remove(0, Directory.GetCurrentDirectory().LastIndexOf("\\") + 1))
            {
                Directory.SetCurrentDirectory("../");
            }
            foreach (var trainingImage in Directory.GetFiles("./kinectElements/faces", "*.png"))
            {
                string rawname = trainingImage.Remove(trainingImage.LastIndexOf(".")).Remove(0, trainingImage.LastIndexOf("\\") + 1);
                this.targetFaces.Add(new BitmapSourceTargetFace
                {
                    Key = rawname,
                    Image = new Bitmap(trainingImage)
                });
            }
            if (this.targetFaces.Count > 1)
                this.engine.SetTargetFaces(this.targetFaces);
            foreach (var trainingImage in Directory.GetFiles("./profiles", "*.txt"))
            {
                this.outputUsers.Add(new OutputUser
                {
                    Name = trainingImage.Remove(trainingImage.LastIndexOf(".")).Remove(0, trainingImage.LastIndexOf("\\") + 1)
                });
            }
            this.Users.ItemsSource = this.outputUsers;
        }

        [DllImport("gdi32")]
        private static extern int DeleteObject(IntPtr o);

        /// <summary>
        /// Loads a bitmap into a bitmap source
        /// </summary>
        private static BitmapSource LoadBitmap(Bitmap source)
        {
            IntPtr ip = source.GetHbitmap();
            BitmapSource bs = null;
            try
            {
                bs = System.Windows.Interop.Imaging.CreateBitmapSourceFromHBitmap(ip,
                   IntPtr.Zero, Int32Rect.Empty,
                   System.Windows.Media.Imaging.BitmapSizeOptions.FromEmptyOptions());
            }
            finally
            {
                DeleteObject(ip);
            }

            return bs;
        }

        /// <summary>
        /// Handles recognition complete events
        /// </summary>
        private void Engine_RecognitionComplete(object sender, RecognitionResult e)
        {
            RecognitionResult.Face face = null;

            if (e.Faces != null)
                face = e.Faces.FirstOrDefault();

            if (face != null)
            {
                if (!string.IsNullOrEmpty(face.Key))
                {
                    // Write the key on the image...
                    using (var g = Graphics.FromImage(e.ProcessedBitmap))
                    {
                        var rect = face.TrackingResults.FaceRect;
                        g.DrawString(face.Key, new Font("Arial", 20), Brushes.Red, new System.Drawing.Point(rect.Left, rect.Top - 25));
                    }
                    if (face.Key.StartsWith("Paul"))
                    {
                        System.Diagnostics.Trace.WriteLine("Paul");
                        System.Windows.Application.Current.Shutdown();
                        return;
                    }
                }
            }

            this.Video.Source = LoadBitmap(e.ProcessedBitmap);
        }


        /// <summary>
        /// Target face with a BitmapSource accessor for the face
        /// </summary>
        private class BitmapSourceTargetFace : TargetFace
        {
            private BitmapSource bitmapSource;

            /// <summary>
            /// Gets the BitmapSource version of the face
            /// </summary>
            public BitmapSource BitmapSource
            {
                get
                {
                    if (this.bitmapSource == null)
                        this.bitmapSource = MainWindow.LoadBitmap(this.Image);

                    return this.bitmapSource;
                }
            }
        }
    }
}
