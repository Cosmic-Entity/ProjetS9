# Projet S9 : Super Resolution

### Dependencies
- Python 3
- [PyTorch >= 1.0](https://pytorch.org/) (CUDA version >= 7.5 if installing with CUDA. [More details](https://pytorch.org/get-started/previous-versions/))
- Python packages:  `pip install numpy opencv-python`
- NVIDIA GPU + [CUDA](https://developer.nvidia.com/cuda-downloads)


### Test models
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

1. Prepare datasets. More details are in [`codes/data`](https://github.com/BlueAmulet/BasicSR/tree/master/codes/data) and [
(Faster IO speed)](https://github.com/xinntao/BasicSR/wiki/Faster-IO-speed). 
1. Choose an existing pretrained ESRGAN model such as `RRDB_ESRGAN_x4.pth`.
1. Modify the configuration file  `options/train/train_esrgan.json`
1. Run command: `python train.py -opt options/train/train_esrgan.json` or in google colab : `%run /content/drive/.../BasicSR-lite/codes/train.py -opt /content/drive/.../BasicSR-lite/codes/options/train/train_template.yml`
