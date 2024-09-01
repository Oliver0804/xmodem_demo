import os
import serial
import sys
from colorama import init, Fore

init(autoreset=True)

SOH = f"{Fore.RED}0x01{Fore.RESET}"
EOT = f"{Fore.GREEN}0x04{Fore.RESET}"
ACK = f"{Fore.YELLOW}0x06{Fore.RESET}"
NAK = f"{Fore.BLUE}0x15{Fore.RESET}"
CAN = f"{Fore.MAGENTA}0x18{Fore.RESET}"

SOH = 0x01
EOT = 0x04
ACK = 0x06
NAK = 0x15
CAN = 0x18



BLOCK_SIZE = 128  # XMODEM-128，每個塊128字節

def checksum(data):
    """計算校驗和"""
    return sum(data) % 256

def send_block(ser, block_number, data, simulate=False):
    """發送一個數據塊"""
    block_number_byte = block_number.to_bytes(1, 'big')
    complement_block_number_byte = (255 - block_number).to_bytes(1, 'big')
    checksum_byte = checksum(data).to_bytes(1, 'big')
    
    block = bytes([SOH]) + block_number_byte + complement_block_number_byte + data + checksum_byte

    soh_colored = f"{Fore.RED}{block[:1].hex()}{Fore.RESET}"
    block_number_colored = f"{Fore.YELLOW}{block[1:2].hex()}{Fore.RESET}"
    complement_colored = f"{Fore.CYAN}{block[2:3].hex()}{Fore.RESET}"
    data_colored = f"{Fore.GREEN}{block[3:-1].hex()}{Fore.RESET}"
    checksum_colored = f"{Fore.BLUE}{block[-1:].hex()}{Fore.RESET}"
    
    print(f"發送塊 #{block_number}")
    print(f"塊內容: {soh_colored}{block_number_colored}{complement_colored}{data_colored}{checksum_colored}")
    print(f"說明: SOH={Fore.RED}0x01{Fore.RESET}, Block Number={Fore.YELLOW}{block_number}{Fore.RESET}, Complement={Fore.CYAN}{255 - block_number}{Fore.RESET}, Checksum={Fore.BLUE}{checksum(data)}{Fore.RESET}\n")

    if simulate:
        return True #  Simulate 模式下不發送數據，直接返回成功
    else:
        ser.write(block)
        response = ser.read(1)
    
    return response == bytes([ACK])

def xmodem_send(ser, filename, simulate=False):
    """通過XMODEM協議傳輸文件"""
    block_number = 1
    total_bytes_sent = 0
    
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BLOCK_SIZE)
            if len(data) == 0:
                break
            
            # 填充數據塊至128字節
            if len(data) < BLOCK_SIZE:
                data += bytes([0x1A] * (BLOCK_SIZE - len(data)))  # 0x1A 表示EOF

            while not send_block(ser, block_number, data, simulate=simulate):
                if not simulate:
                    ser.write(bytes([NAK]))
                    
            total_bytes_sent += len(data)
            block_number += 1
    
    # 傳輸結束
    if simulate:
        print("發送結束 (EOT)")
        print(f"說明: EOT={EOT}")
        
    else:
        ser.write(bytes([EOT]))
        if ser.read(1) == bytes([ACK]):
            print("傳輸完成")
        else:
            print("傳輸失敗")
    
    print(f"共發送 {total_bytes_sent} bytes")

def receive_block(ser, simulate=False):
    """接收一個數據塊"""
    block_header = ser.read(1)
    
    if block_header == bytes([SOH]):
        block_number = int.from_bytes(ser.read(1), 'big')
        complement_block_number = int.from_bytes(ser.read(1), 'big')
        
        if block_number + complement_block_number != 255:
            if not simulate:
                ser.write(bytes([NAK]))
            return None, False
        
        data = ser.read(BLOCK_SIZE)
        received_checksum = int.from_bytes(ser.read(1), 'big')

        if simulate:
            print(f"接收塊 #{block_number}")
            print(f"塊內容: {data.hex()}")
            print(f"說明: Block Number={block_number}, Complement={complement_block_number}, Checksum={received_checksum}")
        
        if checksum(data) == received_checksum:
            if not simulate:
                ser.write(bytes([ACK]))
            return data, True
        else:
            if not simulate:
                ser.write(bytes([NAK]))
            return None, False
    
    elif block_header == bytes([EOT]):
        if simulate:
            print("接收結束 (EOT)")
            print(f"說明: EOT={EOT}")
        else:
            ser.write(bytes([ACK]))
        return None, True
    
    else:
        if not simulate:
            ser.write(bytes([NAK]))
        return None, False

def xmodem_receive(ser, filename, simulate=False):
    """接收文件並保存到本地"""
    block_number = 1
    
    with open(filename, 'wb') as f:
        while True:
            data, success = receive_block(ser, simulate=simulate)
            
            if data is None:
                if success:  # EOT 已接收，傳輸完成
                    print("接收完成")
                    break
                else:
                    print("接收失敗，重試中...")
            else:
                if len(data) > 0 and not simulate:
                    f.write(data)
                block_number += 1

def main(mode, port, baudrate, filename, simulate):
    # 計算文件大小
    file_size = os.path.getsize(filename)
    print(f"{Fore.CYAN}文件大小: {file_size} bytes")

    # 計算預估傳輸時間
    bits_per_byte = 10  # 1 start bit + 8 data bits + 1 stop bit
    total_bits = file_size * bits_per_byte
    estimated_time = total_bits / baudrate
    print(f"{Fore.CYAN}預估傳輸時間: {estimated_time:.2f} 秒")

    # 模擬模式下不打開串行端口
    ser = None
    if not simulate:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)

    if mode == 'send':
        xmodem_send(ser, filename, simulate=simulate)
    elif mode == 'receive':
        xmodem_receive(ser, filename, simulate=simulate)
    else:
        print("未知模式，請選擇 'send' 或 'receive'。")
    
    if ser:
        ser.close()

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print(f"{Fore.RED}使用方法: python xmodem_transfer.py <模式> <串行端口> <波特率> <文件名> <模擬模式>")
        print(f"{Fore.RED}模式: 'send' 或 'receive'")
        print(f"{Fore.RED}模擬模式: 'simulate' 或 'real'")
        sys.exit(1)

    mode = sys.argv[1]
    port = sys.argv[2]
    baudrate = int(sys.argv[3])
    filename = sys.argv[4]
    simulate = sys.argv[5].lower() == 'simulate'

    main(mode, port, baudrate, filename, simulate)