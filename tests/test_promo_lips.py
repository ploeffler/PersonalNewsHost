import array
from pathlib import Path
import tempfile
import unittest
import wave
from PIL import Image, ImageDraw, ImageChops
from scripts.promo_lips import locate_lips,animate,speech_envelope,mouth_box

class LipsTests(unittest.TestCase):
    def image(self):
        image=Image.new('RGB',(200,100),'#dbab90');d=ImageDraw.Draw(image)
        d.ellipse((65,48,95,60),fill='#a51055');d.ellipse((140,48,180,65),fill='#a51055')
        return image
    def test_selected_roi_excludes_second_presenter(self):
        image=self.image();mouth=locate_lips(image,{'x':.4,'y':.55,'width':.3,'height':.28})
        self.assertAlmostEqual(mouth['x'],.4,delta=.02)
        self.assertLess(mouth_box(image,mouth)[2],120)
    def test_ambiguous_or_missing_lips_stop_instead_of_guess(self):
        with self.assertRaises(ValueError):locate_lips(Image.new('RGB',(200,100),'gray'),{'x':.4,'y':.5,'width':.3,'height':.2})
    def test_rest_is_exact_and_motion_local_to_calibrated_face(self):
        image=self.image();mouth={'x':.4,'y':.55,'width':.16,'height':.14}
        self.assertEqual(animate(image,mouth,0).tobytes(),image.convert('RGBA').tobytes())
        moved=animate(image,mouth,1)
        self.assertNotEqual(moved.tobytes(),image.convert('RGBA').tobytes())
        self.assertEqual(moved.crop((130,0,200,100)).tobytes(),image.convert('RGBA').crop((130,0,200,100)).tobytes())
    def test_nan_edge_and_zero_rectangles_rejected(self):
        for x in [float('nan'),0,1]:
            with self.assertRaises(ValueError):mouth_box(self.image(),dict(x=x,y=.5,width=.1,height=.1))
    def test_silence_closes_after_speech(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'speech.wav';samples=array.array('h',[0]*8000+[int(10000*((i%20)/10-1)) for i in range(8000)]+[0]*8000)
            with wave.open(str(path),'wb') as wav:
                wav.setparams((1,2,16000,0,'NONE','not compressed'));wav.writeframes(samples.tobytes())
            envelope=speech_envelope(path,20)
            self.assertEqual(envelope[:8],[0]*8);self.assertGreater(max(envelope),.5);self.assertEqual(envelope[-8:],[0]*8)
