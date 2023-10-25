# ePDFpy
ePDFpy is a python based open-source software for electron pair distribution function (PDF) analysis of amorphous materials to study their local structure. The software is a multi-platform and standalone program that can extract PDF from image file without any other program. ePDFpy enhanced center finding process and introduced elliptical error correction of image to get better quality of the intensity profile. These are all automated so it doesn’t necessary require a user input. In addition, batch process help user analyze multiple files at once.
![alt text](https://github.com/pilsungdev/ePDFpy/blob/master/assets/screenshots/profile_extraction.png?raw=true)
![alt text](https://github.com/pilsungdev/ePDFpy/blob/master/assets/screenshots/pdf_analysis.png?raw=true)


# Installation
[ePDFpy zip file](https://github.com/pilsungdev/ePDFpy/archive/refs/heads/master.zip)
```bash
# Download source code. If you don't use git, download above zip file and unpack instead of below command.
git clone https://github.com/pilsungdev/ePDFpy.git

# enter into the folder
cd ePDFpy

# install required libraries
pip install -r requirements.txt
```
# run
```bash
python -m run_ui.py
```