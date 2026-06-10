import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import currency_fetcher as cf

class CurrencyTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Price Tracker")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Available currencies
        self.currencies = ['USD', 'EUR', 'AFN', 'TJS', 'TRY']
        
        # Selected currencies
        self.currency1 = tk.StringVar(value='USD')
        self.currency2 = tk.StringVar(value='EUR')
        
        # Flag to control auto-refresh
        self.auto_refresh = True
        
        self.setup_ui()
        self.start_auto_refresh()
    
    def setup_ui(self):
        """Create the user interface"""
        
        # Title
        title_label = tk.Label(
            self.root, 
            text="💱 Currency Price Tracker", 
            font=("Arial", 20, "bold"),
            bg='#f0f0f0'
        )
        title_label.pack(pady=10)
        
        # Control Panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10, padx=10, fill='x')
        
        # Currency selection
        ttk.Label(control_frame, text="Select Currencies:").pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="Currency 1:").pack(side='left', padx=5)
        combo1 = ttk.Combobox(
            control_frame, 
            textvariable=self.currency1, 
            values=self.currencies,
            width=10,
            state='readonly'
        )
        combo1.pack(side='left', padx=5)
        combo1.bind('<<ComboboxSelected>>', lambda e: self.manual_refresh())
        
        ttk.Label(control_frame, text="Currency 2:").pack(side='left', padx=5)
        combo2 = ttk.Combobox(
            control_frame, 
            textvariable=self.currency2, 
            values=self.currencies,
            width=10,
            state='readonly'
        )
        combo2.pack(side='left', padx=5)
        combo2.bind('<<ComboboxSelected>>', lambda e: self.manual_refresh())
        
        # Buttons
        refresh_btn = ttk.Button(control_frame, text="🔄 Refresh Now", command=self.manual_refresh)
        refresh_btn.pack(side='left', padx=5)
        
        graph_btn = ttk.Button(control_frame, text="📊 Show 30-Day Graph", command=self.show_graph)
        graph_btn.pack(side='left', padx=5)
        
        # Main content frame with two columns
        main_frame = ttk.Frame(self.root)
        main_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Left column - Info and table
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # Info Display
        info_frame = ttk.LabelFrame(left_frame, text="Current Exchange Rate", padding=10)
        info_frame.pack(pady=10, fill='x')
        
        self.info_label = tk.Label(
            info_frame,
            text="Loading data...",
            font=("Arial", 14),
            bg='white',
            fg='#333',
            relief='sunken',
            padx=10,
            pady=10
        )
        self.info_label.pack(fill='both')
        
        # Status
        self.status_label = tk.Label(
            left_frame,
            text="Status: Initializing...",
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#666'
        )
        self.status_label.pack(pady=5)
        
        # Data Display
        data_frame = ttk.LabelFrame(left_frame, text="Recent Prices", padding=10)
        data_frame.pack(pady=10, fill='both', expand=True)
        
        # Treeview for data
        columns = ('Timestamp', 'Currency 1', 'Currency 2')
        self.tree = ttk.Treeview(data_frame, columns=columns, height=10, show='headings')
        
        for col in columns:
            self.tree.column(col, width=300)
            self.tree.heading(col, text=col)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(data_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Right column - Prediction
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', padx=5)
        
        # Prediction Display
        prediction_frame = ttk.LabelFrame(right_frame, text="🤖 AI Prediction (Tomorrow)", padding=15)
        prediction_frame.pack(pady=10, fill='both')
        
        self.prediction_label = tk.Label(
            prediction_frame,
            text="Collecting data...\n\nPlease wait",
            font=("Arial", 12),
            bg='#e8f4f8',
            fg='#333',
            relief='sunken',
            padx=15,
            pady=15,
            wraplength=250,
            justify='left'
        )
        self.prediction_label.pack(fill='both', expand=True)
    
    def manual_refresh(self):
        """Manually refresh data"""
        threading.Thread(target=self._refresh_data, daemon=True).start()
    
    def _refresh_data(self):
        """Fetch and update data"""
        try:
            # Fetch prices
            prices = cf.fetch_current_prices(self.currencies)
            
            if prices:
                # Save to database
                cf.save_price_data(prices)
                
                # Update UI
                self.update_display(prices)
                self.update_prediction()
                self.update_status("✅ Data updated successfully!")
            else:
                self.update_status("❌ Failed to fetch prices")
        
        except Exception as e:
            print(f"Error in _refresh_data: {e}")
            self.update_status(f"❌ Error: {str(e)}")
    
    def update_display(self, prices):
        """Update the information display"""
        try:
            c1 = self.currency1.get()
            c2 = self.currency2.get()
            
            if c1 in prices and c2 in prices and prices[c1] and prices[c2]:
                rate = prices[c1] / prices[c2]
                
                # Get price change
                current_rate, change = cf.get_price_change(c1, c2)
                
                change_text = ""
                if change is not None:
                    change_text = f" ({change:+.2f}%)" if change != 0 else " (No change)"
                
                # Update info label
                info_text = f"1 {c1} = {rate:.6f} {c2}{change_text}\n\nPrice: {prices[c1]:.6f} / {prices[c2]:.6f}"
                self.info_label.config(text=info_text)
                
                # Update table
                self.update_table(prices)
        except Exception as e:
            print(f"Error in update_display: {e}")
    
    def update_table(self, prices):
        """Update the data table"""
        try:
            # Clear table
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get historical data
            historical = cf.get_historical_data(days=30)
            
            if not historical:
                print("No historical data available yet")
                return
            
            # Display last 10 entries
            c1 = self.currency1.get()
            c2 = self.currency2.get()
            
            count = 0
            for timestamp, price_data in sorted(historical.items())[-10:]:
                if c1 in price_data and c2 in price_data:
                    if price_data[c1] and price_data[c2]:
                        self.tree.insert('', 0, values=(
                            timestamp,
                            f"{price_data[c1]:.6f}",
                            f"{price_data[c2]:.6f}"
                        ))
                        count += 1
            
            print(f"Added {count} rows to table")
        except Exception as e:
            print(f"Error in update_table: {e}")
    
    def update_prediction(self):
        """Update price prediction"""
        try:
            c1 = self.currency1.get()
            c2 = self.currency2.get()
            
            prediction = cf.predict_future_price(c1, c2, days_ahead=1)
            
            if prediction:
                predicted_rate = prediction['predicted_rate']
                current_rate = prediction['current_rate']
                percentage_change = prediction['percentage_change']
                confidence = prediction['confidence']
                trend = prediction['trend']
                data_points = prediction['data_points']
                
                # Format prediction text
                prediction_text = f"""
قیمت کنونی:
1 {c1} = {current_rate:.6f} {c2}

پیش‌بینی فردا:
1 {c1} = {predicted_rate:.6f} {c2}

تغییر:
{percentage_change:+.2f}%

روند:
{trend}

اعتماد:
{confidence}% ✓

داده‌ها:
{data_points} نقطه
""".strip()
                
                self.prediction_label.config(text=prediction_text)
            else:
                self.prediction_label.config(
                    text="⏳ در حال جمع‌آوری داده...\n\nلطفا صبر کنید\n\n(حداقل 3 داده نیاز است)"
                )
        
        except Exception as e:
            print(f"Error in update_prediction: {e}")
            self.prediction_label.config(text=f"❌ خطا:\n{str(e)}")
    
    def update_status(self, message):
        """Update status label"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"[{timestamp}] {message}")
    
    def show_graph(self):
        """Show 30-day price chart"""
        try:
            c1 = self.currency1.get()
            c2 = self.currency2.get()
            
            print(f"Getting historical data for {c1}/{c2}")
            historical = cf.get_historical_data(days=30)
            
            print(f"Historical data entries: {len(historical)}")
            
            if not historical or len(historical) == 0:
                messagebox.showwarning(
                    "No Data", 
                    "No historical data available yet.\n\n"
                    "Please wait at least a few minutes for data to be collected.\n"
                    "The app saves data automatically every 60 seconds."
                )
                return
            
            # Prepare data
            timestamps = []
            rates = []
            
            for timestamp, prices in sorted(historical.items()):
                if c1 in prices and c2 in prices and prices[c1] and prices[c2]:
                    try:
                        timestamps.append(timestamp)
                        rate = prices[c1] / prices[c2]
                        rates.append(rate)
                    except Exception as e:
                        print(f"Error processing entry {timestamp}: {e}")
                        continue
            
            print(f"Chart data points: {len(rates)}")
            
            if not rates or len(rates) == 0:
                messagebox.showwarning("No Data", "No valid data for selected currencies.")
                return
            
            # Create new window for graph
            graph_window = tk.Toplevel(self.root)
            graph_window.title(f"{c1}/{c2} - 30 Day Chart")
            graph_window.geometry("1000x600")
            
            # Create figure
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            ax.plot(range(len(rates)), rates, marker='o', linestyle='-', color='#0066cc', linewidth=2)
            ax.set_xlabel('Data Points', fontsize=10)
            ax.set_ylabel(f'Exchange Rate ({c1}/{c2})', fontsize=10)
            ax.set_title(f'{c1}/{c2} - Historical Data ({len(rates)} entries)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Show every Nth timestamp to avoid crowding
            step = max(1, len(timestamps) // 6)
            tick_positions = range(0, len(timestamps), step)
            tick_labels = [timestamps[i] if i < len(timestamps) else '' for i in tick_positions]
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels, rotation=45, ha='right')
            
            fig.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, master=graph_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)
            
            self.update_status(f"📊 Showing {c1}/{c2} chart with {len(rates)} data points")
            
        except Exception as e:
            print(f"Error in show_graph: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Error creating graph:\n{str(e)}")
    
    def start_auto_refresh(self):
        """Auto-refresh data every 60 seconds"""
        def auto_refresh_loop():
            while self.auto_refresh:
                time.sleep(60)  # Wait 60 seconds
                print("Auto-refreshing data...")
                self._refresh_data()
        
        threading.Thread(target=auto_refresh_loop, daemon=True).start()
        
        # Initial refresh
        print("Starting initial refresh...")
        self.manual_refresh()
    
    def on_closing(self):
        """Handle window closing"""
        self.auto_refresh = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyTrackerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
