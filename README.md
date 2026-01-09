
# 🧪 Universal Testing Machine Controller (UTM-GUI)

This project is a fully modular and advanced **Python desktop GUI** for controlling a **Universal Testing Machine (UTM)** powered by Arduino. It features:

- 🔄 Bi-directional communication with Arduino via serial
- Real-time plotting of force, displacement, and stress-strain curves
- Material property calculation (Young’s Modulus, Yield Strength, etc.)
- Machine control via GUI and PCB hardware buttons
- Clean modular architecture for easy team collaboration and feature updates

---

## 👨‍💻 Project Structure

```
utm-controller/
│
├── main.py                  # Entry point
├── utm_controller.py        # Central controller managing GUI and logic
├── gui_components.py        # UI panels (buttons, displays, speed control)
├── graph_plotter.py         # Real-time and analysis plotting
├── serial_handler.py        # Arduino serial communication manager
├── config.py                # Configurable constants and themes
├── utils.py                 # Shared helpers (ports, logging, file export)
└── pyproject.toml           # Project dependencies
```

---

## 👥 Team Collaboration Notes

- 💡 All core modules are **modularized** to allow parallel development.
- 🛠️ For UI updates, modify `gui_components.py` or `graph_plotter.py`.
- ⚙️ Update `config.py` for constants (e.g., limits, materials, port defaults).
- 🚦 Run `main.py` to launch the application.

---

## 📦 Dependencies

- Python 3.11+
- `matplotlib`, `scipy`, `pyserial`, `numpy`
- (Recommended) [`ttkbootstrap`](https://ttkbootstrap.readthedocs.io) for modern UI themes

Install all with:

```bash
pip install -r requirements.txt
```

---

## 📌 TODO (for contributors)

- [ ] Add dark mode toggle  
- [ ] Improve UI responsiveness  
- [ ] Add calibration workflow  
- [ ] Implement data report export to PDF  
- [ ] Add sensor calibration tab

---

## 📄 License

MIT License / CC-BY-NC-SA depending on usage.

---

> Made with ❤️ by the UTM Development Team

