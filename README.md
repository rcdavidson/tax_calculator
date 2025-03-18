# UK Tax Calculator

A web application that calculates UK income tax, National Insurance contributions, student loan repayments, and pension contributions based on annual salary.

## Features

- Calculates income tax based on 2023/24 tax bands (20%, 40%, 45%)
- Calculates National Insurance contributions
- Supports student loan repayments (Plan 1, Plan 2, Plan 4, and Postgraduate)
- Handles pension contributions (as percentage or fixed amount)
- Provides detailed monthly breakdown of deductions

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/tax_calculator.git
   cd tax_calculator
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5001
   ```

3. Enter your annual salary, pension contributions, and student loan plan to calculate your take-home pay.

## Deployment

This application can be deployed to platforms like Heroku, Render, or any other service that supports Python/Flask applications.

## License

[MIT License](LICENSE) 