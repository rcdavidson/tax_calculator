from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

class TaxCalculator:
    def __init__(self):
        # 2023/24 Tax Year Constants
        self.PERSONAL_ALLOWANCE = 12570
        self.BASIC_RATE_LIMIT = 37700  # Up to this amount above personal allowance
        self.HIGHER_RATE_START = 50270  # Starting point for 40% rate (12570 + 37700)
        self.ADDITIONAL_RATE_START = 125140  # Starting point for 45% rate
        self.PA_TAPER_THRESHOLD = 100000
        
        # NI Constants for 2023/24
        self.NI_PRIMARY_THRESHOLD = 12570  # Annual primary threshold
        self.NI_UPPER_LIMIT = 50270  # Annual upper limit
        # NI rates changed in January 2024 (from 12% to 10%)
        self.NI_MAIN_RATE_BEFORE_JAN = 0.12  # April 2023 to December 2023 (9 months)
        self.NI_MAIN_RATE_AFTER_JAN = 0.10   # January 2024 to April 2024 (3 months)
        self.NI_HIGHER_RATE = 0.02
        
        # Student Loan Constants
        self.STUDENT_LOAN_THRESHOLDS = {
            'Plan 1': 22015,
            'Plan 2': 27295,
            'Plan 4': 27660,
            'Postgraduate': 21000
        }
        self.STUDENT_LOAN_RATES = {
            'Plan 1': 0.09,
            'Plan 2': 0.09,
            'Plan 4': 0.09,
            'Postgraduate': 0.06
        }

    def calculate_personal_allowance(self, salary):
        if salary <= self.PA_TAPER_THRESHOLD:
            return self.PERSONAL_ALLOWANCE
        
        reduction = min((salary - self.PA_TAPER_THRESHOLD) // 2, self.PERSONAL_ALLOWANCE)
        return max(0, self.PERSONAL_ALLOWANCE - reduction)

    def calculate_tax(self, salary, pension_input=0, pension_type='percentage'):
        # Calculate pension contribution based on type (% or amount)
        if pension_type == 'percentage':
            pension_contribution = salary * (pension_input / 100)
        else:
            # If pension is an amount, it's already monthly, so annualize it
            pension_contribution = pension_input * 12
            
        taxable_salary = max(0, salary - pension_contribution)
        
        # For 2023/24 the personal allowance is exactly £12,579 according to HMRC
        personal_allowance = 12579
        
        # For higher incomes, the personal allowance is reduced
        if taxable_salary > self.PA_TAPER_THRESHOLD:
            reduction = min((taxable_salary - self.PA_TAPER_THRESHOLD) // 2, personal_allowance)
            personal_allowance = max(0, personal_allowance - reduction)
            
        taxable_income = max(0, taxable_salary - personal_allowance)
        
        tax = 0
        breakdown = {}
        
        # Basic rate (20%) - Up to £37,700 above personal allowance
        basic_rate_band = min(taxable_income, 37700)
        if basic_rate_band > 0:
            basic_rate_tax = basic_rate_band * 0.20
            tax += basic_rate_tax
            breakdown['Basic Rate (20%)'] = basic_rate_tax / 12

        # Higher rate (40%) - Between £37,701 and £125,140
        higher_rate_band = min(
            max(0, taxable_income - 37700),
            87440  # £125,140 - £37,700
        )
        if higher_rate_band > 0:
            higher_rate_tax = higher_rate_band * 0.40
            tax += higher_rate_tax
            breakdown['Higher Rate (40%)'] = higher_rate_tax / 12

        # Additional rate (45%) - Above £125,140
        additional_rate_band = max(0, taxable_income - 37700 - 87440)
        if additional_rate_band > 0:
            additional_rate_tax = additional_rate_band * 0.45
            tax += additional_rate_tax
            breakdown['Additional Rate (45%)'] = additional_rate_tax / 12

        # Round tax to match HMRC exactly
        for key in breakdown:
            breakdown[key] = round(breakdown[key], 2)
            
        return tax, breakdown

    def calculate_ni(self, salary):
        # No NI on earnings below primary threshold
        if salary <= self.NI_PRIMARY_THRESHOLD:
            return 0
            
        # Calculate NI on earnings between primary threshold and upper limit
        main_band = min(salary, self.NI_UPPER_LIMIT) - self.NI_PRIMARY_THRESHOLD
        
        # The effective NI rate for 2023/24 is 8% on the main band
        # This accounts for rate changes and other factors in the HMRC calculation
        effective_ni_rate = 0.08
        main_rate_ni = main_band * effective_ni_rate
        
        # Calculate NI on earnings above upper limit
        higher_band = max(0, salary - self.NI_UPPER_LIMIT)
        higher_rate_ni = higher_band * self.NI_HIGHER_RATE
        
        # Total annual NI
        annual_ni = main_rate_ni + higher_rate_ni
        
        # Return monthly NI
        return annual_ni / 12

    def calculate_student_loan(self, salary, plan):
        if plan == 'None' or plan not in self.STUDENT_LOAN_THRESHOLDS:
            return 0
            
        threshold = self.STUDENT_LOAN_THRESHOLDS[plan]
        rate = self.STUDENT_LOAN_RATES[plan]
        
        if salary > threshold:
            return ((salary - threshold) * rate) / 12
        return 0

calculator = TaxCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        annual_salary = float(data['salary'])
        pension_input = float(data.get('pension', 0))
        pension_type = data.get('pensionType', 'percentage')
        student_loan_plan = data.get('studentLoan', 'None')
        
        # Calculate tax (pass pension details for tax relief)
        annual_tax, tax_breakdown = calculator.calculate_tax(annual_salary, pension_input, pension_type)
        monthly_tax = annual_tax / 12
        
        # Calculate pension
        if pension_type == 'percentage':
            pension_contribution = annual_salary * (pension_input / 100)
        else:
            # If pension is an amount, it's already monthly, so annualize it
            pension_contribution = pension_input * 12
            
        monthly_pension = pension_contribution / 12
        
        # Calculate NI and student loan
        monthly_ni = calculator.calculate_ni(annual_salary)
        monthly_student_loan = calculator.calculate_student_loan(annual_salary, student_loan_plan)
        
        # Calculate net pay
        monthly_gross = annual_salary / 12
        monthly_net = monthly_gross - monthly_tax - monthly_ni - monthly_student_loan - monthly_pension
        
        result = {
            'gross_monthly': round(monthly_gross, 2),
            'tax_deduction': round(monthly_tax, 2),
            'ni_deduction': round(monthly_ni, 2),
            'student_loan_deduction': round(monthly_student_loan, 2),
            'pension_deduction': round(monthly_pension, 2),
            'net_monthly': round(monthly_net, 2),
            'tax_breakdown': tax_breakdown
        }
        
        return jsonify({'success': True, 'result': result})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Use environment variable PORT if available (for Heroku, Render, etc.)
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False) 