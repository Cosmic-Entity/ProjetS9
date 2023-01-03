# Projet S9 : Super Resolution

### Dependencies
- Python 3
- [PyTorch >= 1.0](https://pytorch.org/) (CUDA version >= 7.5 if installing with CUDA. [More details](https://pytorch.org/get-started/previous-versions/))
- Python packages:  `pip install numpy opencv-python`
- NVIDIA GPU + [CUDA](https://developer.nvidia.com/cuda-downloads)


### How to Test the ESRGAN model
1. Clone this github repository.
```
git clone https://github.com/Cosmic-Entity/ProjetS9/ESRGAN
```
2. Place your own low-resolution images in `./LR` folder.
3. Download pretrained models from [Google Drive](https://drive.google.com/drive/u/0/folders/17VYV_SoZZesU6mbxz2dMAIccSSlqLecY) and place them in `./models`.
4. Run command :
```
python test.py
```
   Or if you are running it in google colab from your drive :
```
%run /content/drive/.../ESRGAN/test.py
```
5. The results are in `./results` folder.

### How to Train ESRGAN models

1. Prepare datasets. More details are in [`ESRGAN/Training/BasicSR-lite/codes/data`](https://github.com/Cosmic-Entity/ProjetS9/blob/main/ESRGAN/Training/BasicSR-lite/codes/data)
1. Choose an existing pretrained ESRGAN model such as `RRDB_ESRGAN_x4.pth`.
1. Modify the configuration file  `options/train/train_esrgan.json`
1. Run command: `python train.py -opt options/train/train_esrgan.json` or in google colab : `%run /content/drive/.../BasicSR-lite/codes/train.py -opt /content/drive/.../BasicSR-lite/codes/options/train/train_template.yml`

### What I did

1. First I tested the pretrained ESRGAN model on a huge number of images to identity which type of images show the least satisfactory results. I noticed that the model really struggled with human faces.
2. I ran lots of object classification tests on images before and after Super Resolution using the ESRGAN model in order to figure out the impact of Super Resolution on classification.
3. I tried to train the ESRGAN model with human faces to improve the model's efficiency on images including those features. I prepared a dataset of croped images of NBA player Lebron James. I interrupted the training process after more than 2h because I realised it would take 2 days for it to be done. The google colab GPU just wasn't powerful enough.


### Bibliography

Link to the original ESRGAN git repository : https://github.com/xinntao/ESRGAN
