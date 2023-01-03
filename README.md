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
4. Run the test.py file :
```
python test.py
```
5. The results are in `./results` folder.

### How to Train ESRGAN/SRGAN models
We use a PSNR-oriented pretrained SR model to initialize the parameters for better quality. According to the author's paper and some testing, this will also stabilize the GAN training and allows for faster convergence. 

1. Prepare datasets, usually the DIV2K dataset. More details are in [`codes/data`](https://github.com/BlueAmulet/BasicSR/tree/master/codes/data) and [
(Faster IO speed)](https://github.com/xinntao/BasicSR/wiki/Faster-IO-speed). 
1. Optional: If the intention is to replicate the original paper here you would prepare the PSNR-oriented pretrained model. You can also use the original `RRDB_PSNR_x4.pth` as the pretrained model for that purpose, otherwise *any* existing model will work as pretrained.
1. Modify the configuration file  `options/train/train_esrgan.json`
1. Run command: `python train.py -opt options/train/train_esrgan.json`
