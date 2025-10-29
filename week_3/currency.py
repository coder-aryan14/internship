def usd_to_inr(usd):
    return usd * 83.2  

def inr_to_usd(inr):
    return inr / 83.2

amount = float(input("Enter amount: "))
print("In INR:", usd_to_inr(amount))
