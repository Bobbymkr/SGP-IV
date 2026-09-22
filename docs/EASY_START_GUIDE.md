# Easy Start Guide - Adaptive Traffic Signal Timer

**Made for everyone! No technical experience needed.**

---

## What This Project Does

This smart traffic system:
- Counts cars, buses, trucks, bikes at traffic signals
- Changes traffic light timing based on traffic
- Shows a visual simulation of traffic flow
- Displays real-time traffic statistics

---

## What You'll Need (Simple Checklist)

PASS **Computer** (Windows, Mac, or Linux)
PASS **Internet connection**
PASS **Python** (we'll help you install this)
PASS **15 minutes** of your time

---

## Quick Setup (Choose Your System)

### **For Windows Users**

#### Step 1: Install Python
1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.12" button
3. Run the downloaded file
4. **IMPORTANT:** Check the box that says "Add Python to PATH"
5. Click "Install Now"

#### Step 2: Get the Project Files
1. Open Command Prompt (press Windows key + R, type `cmd`, press Enter)
2. Copy and paste these commands one by one:

```bash
cd Desktop
git clone https://github.com/Bobbymkr/Updated-SGP.git
cd Updated-SGP
```

#### Step 3: Install Required Programs
```bash
cd Code/YOLO/darkflow
pip install tensorflow opencv-python pygame matplotlib Pillow numpy
```

#### Step 4: Run the Demo!
```bash
python run_project.py --demo
```

---

### **For Mac Users**

#### Step 1: Install Python
1. Open Terminal (press Command + Space, type `Terminal`, press Enter)
2. Copy and paste this command:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
3. Then install Python:
```bash
brew install python3
```

#### Step 2: Get the Project Files
```bash
cd Desktop
git clone https://github.com/Bobbymkr/Updated-SGP.git
cd Updated-SGP
```

#### Step 3: Install Required Programs
```bash
cd Code/YOLO/darkflow
pip3 install tensorflow opencv-python pygame matplotlib Pillow numpy
```

#### Step 4: Run the Demo!
```bash
python3 run_project.py --demo
```

---

### **For Linux Users**

#### Step 1: Install Python
1. Open Terminal (press Ctrl + Alt + T)
2. Copy and paste these commands:
```bash
sudo apt update
sudo apt install python3 python3-pip git
```

#### Step 2: Get the Project Files
```bash
cd Desktop
git clone https://github.com/Bobbymkr/Updated-SGP.git
cd Updated-SGP
```

#### Step 3: Install Required Programs
```bash
cd Code/YOLO/darkflow
pip3 install tensorflow opencv-python pygame matplotlib Pillow numpy
```

#### Step 4: Run the Demo!
```bash
python3 run_project.py --demo
```

---

## What You'll See

### **Part 1: Vehicle Detection**
- The system will process 3 traffic images
- You'll see boxes drawn around detected vehicles
- Counts will show: cars, bikes, buses, trucks, rickshaws
- Output images saved in `output_images/` folder

### **Part 2: Traffic Simulation**
- A colorful traffic intersection will appear
- Vehicles will move through the intersection
- Traffic lights will change colors automatically
- You'll see real-time statistics on screen
- The simulation runs for about 2 minutes

---

## Other Things You Can Try

### **Run Just Vehicle Detection**
```bash
# Windows
python run_project.py --detection

# Mac/Linux
python3 run_project.py --detection
```

### **Run Just Traffic Simulation**
```bash
# Windows
python run_project.py --simulation

# Mac/Linux
python3 run_project.py --simulation
```

### **See Project Information**
```bash
# Windows
python run_project.py --info

# Mac/Linux
python3 run_project.py --info
```

---

## Troubleshooting (Common Problems)

### **Problem: "python is not recognized"**
**Solution:** Make sure you checked "Add Python to PATH" during installation. Then restart Command Prompt/Terminal.

### **Problem: "pip is not recognized"**
**Solution:** Try using `python -m pip` instead of `pip` (Windows) or `python3 -m pip` instead of `pip3` (Mac/Linux).

### **Problem: "git is not recognized"**
**Solution:** Install Git from https://git-scm.com/downloads and restart your terminal.

### **Problem: "Permission denied"**
**Solution:** Try adding `sudo` before the command (Mac/Linux only).

### **Problem: "ModuleNotFoundError"**
**Solution:** Make sure you're in the correct folder. Type `cd Code/YOLO/darkflow` before running the install command.

### **Problem: Simulation window closes immediately**
**Solution:** This is normal! The simulation runs automatically and closes when finished. Watch it while it's running.

---

## Where to Find Your Results

After running the demo:

- **Vehicle Detection Results:** `Code/YOLO/darkflow/output_images/`
- **Test Images:** `Code/YOLO/darkflow/test_images/`
- **Main Program:** `Code/YOLO/darkflow/run_project.py`

---

## Success!

**Congratulations!** You've successfully run the Adaptive Traffic Signal Timer.

You've seen:
- PASS Smart vehicle detection
- PASS Adaptive traffic signal timing
- PASS Real-time traffic simulation
- PASS Traffic statistics and analytics

---

## Need More Help?

If you run into any issues:
1. Check the troubleshooting section above
2. Make sure you copied commands exactly as shown
3. Ensure you're in the correct folder (`Code/YOLO/darkflow`)
4. Try restarting your terminal/command prompt

**Remember:** This project is designed to be user-friendly. Don't worry about making mistakes - you can always start over!

---

## What's Next?

Now that you've got it running, you can:
- Read the full documentation in `readme.md`
- Run the comprehensive tests with `python run_tests.py`
- Explore advanced features in the `Code/YOLO/darkflow/` folder
- Try the Docker version for easy deployment

**Happy Traffic Management!**

---

*Last Updated: November 2025*
*Made for Non-Technical Users*
*Questions? Check the main project repository!*
