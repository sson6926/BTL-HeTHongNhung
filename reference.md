**HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG KHOA CÔNG NGHỆ THÔNG TIN** 

**BÁO CÁO BÀI TẬP LỚN HỌC PHẦN: XÂY DỰNG CÁC HỆ THỐNG NHÚNG** 

**ĐỀ TÀI: XÂY DỰNG HỆ THỐNG GIÁM SÁT VÀ ĐIỀU KHIỂN MÔI TRƯỜNG TỰ ĐỘNG CHO MÔ HÌNH NUÔI TRỒNG THỦY SẢN** 

**Giảng viên hướng dẫn : Đỗ Tiến Dũng Nhóm lớp : 05 Nhóm bài tập lớn : 07 Thành viên B22DCCN119 : Nguyễn Công Duẩn B21DCCN456 : Nguyễn Quốc Khánh B22DCCN503 : Nguyễn Thanh Long B22DCCN695 : Nguyễn Ngọc Sơn** _**Hà Nội – 2026**_ ~~—~~ 1 

## **MỤC LỤC** 

CHƯƠNG 1: TỔNG QUAN DỰ ÁN .................................................................... 7 1.1. Giới thiệu dự án ........................................................................................... 7 1.2. Các chức năng chính .................................................................................... 7 1.3. Mục tiêu dự án ............................................................................................. 8 CHƯƠNG 2: THIẾT KẾ HỆ THỐNG ................................................................... 9 2.1. Phân tích yêu cầu hệ thống .......................................................................... 9 2.1.1. Yêu cầu chức năng ......................................................................................... 9 2.1.2. Yêu cầu phi chức năng ................................................................................... 9 2.2. Thiết kế vật lý ............................................................................................ 10 2.2.1. Vi điều khiển ESP32 .................................................................................... 11 2.2.2. Cảm biến nhiệt độ DS18B20 ........................................................................ 12 2.2.3. LED 5mm ..................................................................................................... 13 2.2.4. Cảm Biến Siêu Âm HC-SR04 ...................................................................... 13 2.2.5. Mạch Relay 5V 2 Kênh ................................................................................ 15 2.2.6. Chiết áp đơn .................................................................................................. 16 2.2.7. Breadboard và dây nối .................................................................................. 17 2.2.8. Ống nước ...................................................................................................... 18 2.2.9. Máy bơm ....................................................................................................... 19 2.2.10. Cảm biến chất lượng nước TDS ................................................................. 20 2.2.11. Cảm biến độ đục của nước (TS-300B) ....................................................... 21 2.2.12. Thiết kế mạch ............................................................................................. 23 2.3. Các giao thức truyền thông ........................................................................ 24 2.3.1. MQTT ........................................................................................................... 24 2.3.2. HTTP ............................................................................................................ 24 2.4. Thiết kế phần mềm .................................................................................... 25 2.4.1. Kiến trúc tổng quan ...................................................................................... 25 2.4.2. Công nghệ sử dụng ....................................................................................... 25 2.5. Thiết kế logic ............................................................................................. 28 2.5.1. Biểu đồ use case toàn hệ thống..................................................................... 28 2.5.2. Thiết kế chi tiết ............................................................................................. 29 

2 

2.5.3. Thiết kế cơ sở dữ liệu ................................................................................... 31 CHƯƠNG 3: XÂY DỰNG AI SERVICE............................................................ 35 3.1. Giới thiệu bài toán ..................................................................................... 35 3.2. Phân tích dữ liệu đầu vào ........................................................................... 36 3.2.1. Cấu trúc bộ dữ liệu ....................................................................................... 36 3.2.2. Ý nghĩa các chỉ số nước ............................................................................... 36 3.3. Tiền xử lý dữ liệu ....................................................................................... 37 3.3.1. Làm sạch dữ liệu........................................................................................... 37 3.3.2. Chuẩn hóa dữ liệu ......................................................................................... 37 3.3.3. Tạo dữ liệu chuỗi thời gian ........................................................................... 38 3.4. Giới thiệu mô hình LSTM ......................................................................... 39 3.4.1. Tổng quan về mô hình LSTM ...................................................................... 39 3.4.2. Cấu trúc của mạng LSTM ............................................................................ 40 3.4.3. Nguyên lý hoạt động của LSTM .................................................................. 41 3.4.4. Ưu điểm của LSTM ...................................................................................... 42 3.4.5. Hạn chế của LSTM ....................................................................................... 42 3.4.6. Lý do lựa chọn LSTM cho đề tài .................................................................. 42 3.5. Xây dựng mô hình LSTM .......................................................................... 43 3.6. Huấn luyện mô hình ................................................................................... 45 3.6.1. Chia dữ liệu .................................................................................................. 45 3.6.2. Tham số huấn luyện ...................................................................................... 46 3.7. Đánh giá mô hình ....................................................................................... 47 3.7.1. Các chỉ số đánh giá ....................................................................................... 47 3.7.2. Kết quả thực nghiệm..................................................................................... 47 3.7.3. Biểu đồ đánh giá ........................................................................................... 48 3.8. Tích hợp AI Service vào hệ thống ............................................................. 49 3.8.1. Kiến trúc AI Service ..................................................................................... 49 3.8.2. Quy trình hoạt động ...................................................................................... 49 3.8.3. Thiết kế API.................................................................................................. 50 CHƯƠNG 4: KẾT QUẢ ....................................................................................... 51 4.1. Kết quả phần mềm ..................................................................................... 51 

3 

4.2. Kết quả phần cứng ..................................................................................... 52 KẾT LUẬN ........................................................................................................... 53 TÀI LIỆU THAM KHẢO .................................................................................... 54 

4 

## **DANH MỤC HÌNH ẢNH** 

**Hình 2.1:** Vi điều khiển ESP32 ............................................................................ 11 **Hình 2.2:** Cảm biến DS18B20 ............................................................................. 12 **Hình 2.3:** LED 5mm ............................................................................................ 13 **Hình 2.4:** Cảm Biến Siêu Âm HC-SR04 ............................................................. 15 **Hình 2.5:** Mạch Relay 5V 2 Kênh ....................................................................... 16 **Hình 2.6:** Chiết áp đơn ......................................................................................... 17 **Hình 2.7:** Breadboard ........................................................................................... 17 **Hình 2.8:** Dây nối ................................................................................................. 18 **Hình 2.9:** Ống nước .............................................................................................. 19 **Hình 2.10:** Máy bơm ............................................................................................ 20 **Hình 2.11:** Cảm biến chất lượng nước TDS ........................................................ 21 **Hình 2.12:** Cảm biến độ đục của nước (TS-300B) .............................................. 22 **Hình 2.13:** Sơ đồ nối dây thiết kế ........................................................................ 23 **Hình 2.14:** Minh họa thực tế ................................................................................ 23 **Hình 2.15:** Kiến trúc tổng quan............................................................................ 25 **Hình 2.16:** Biểu đồ use case ................................................................................. 28 **Hình 2.17:** Biểu đồ tuần tự của chức năng nhận và lưu liệu cảm biến ................ 29 **Hình 2.18:** Biều đồ tuần tự cho chức năng điều khiển thiết bị ............................ 30 **Hình 2.19:** Cơ sở dữ liệu hệ thống ....................................................................... 31 **Hình 3.1:** Cấu trúc của mạng LSTM .................................................................... 40 **Hình 3.2:** Mô hình LSTM .................................................................................... 44 **Hình 3.3:** Biểu đồ Loss ........................................................................................ 48 **Hình 3.4:** Biểu đồ giá trị dự đoán ........................................................................ 49 **Hình 3.5:** Kiến trúc AI Service ............................................................................ 49 **Hình 4.1:** Giao diện bảng điều khiển ................................................................... 51 **Hình 4.2:** Kết quả lắp mạch thực tế ..................................................................... 52 

5 

## **DANH MỤC TỪ VIẾT TẮT** 

|**Từ viết tắt**|**Thuật ngữ tiếng Anh**|**Thuật ngữ tiếng Việt**|
|---|---|---|
|ADC|Analog-to-Digital Converter|Bộ chuyển đổi tương tự sang số,|
|AI|Artificial Intelligence|Trí tuệ nhân tạo|
|API|Application Programming Interface|Giao diện lập trình ứng dụng|
|BLE|Bluetooth Low Energy|Bluetooth năng lượng thấp|
|CPU|Central Processing Unit|Bộ xử lý trung tâm|
|GPIO|General Purpose Input/Output|Cổng vào/ra đa dụng|
|HTTP|HyperText Transfer Protocol|Giao thức truyền tải siêu văn bản|
|IoT|Internet of Things|Internet vạn vật|
|LED|Light Emitting Diode|Điốt phát quang|
|LSTM|Long Short-Term Memory|Bộ nhớ dài - ngắn|
|MAE|Mean Absolute Error|Sai số tuyệt đối trung bình|
|MEMS|Micro-Electro-Mechanical Systems|Hệ vi cơ điện tử|
|MQTT|Message Queuing Telemetry Transport|Giao thức truyền tải dữ liệu qua hàng đợi<br>thông điệp|
|MSE|Mean Squared Error|Sai số bình phương trung bình|
|ORM|Object Relational Mapping|Ánh xạ quan hệ – đối tượng|
|PWM|Pulse Width Modulation|Điều chế độ rộng xung|
|RAM|Random Access Memory|Bộ nhớ truy cập ngẫu nhiên|
|RDBMS|Relational Database Management<br>System|Hệ quản trị cơ sở dữ liệu quan hệ|
|RMSE|Root Mean Squared Error|Căn bậc hai sai số bình phương trung bình|
|RNN|Recurrent Neural Network|Mạng nơ-ron hồi tiếp|
|SQL|Structured Query Language|Ngôn ngữ truy vấn có cấu trúc|
|TDS|Total Dissolved Solids|Tổng lượng chất rắn hòa tan|
|UI|User Interface|Giao diện người dùng|



6 

## **CHƯƠNG 1: TỔNG QUAN DỰ ÁN** 

## **1.1. Giới thiệu dự án** 

Hệ thống giám sát và điều khiển môi trường nuôi trồng thủy sản là một ứng dụng tiêu biểu của hệ thống nhúng và IoT trong lĩnh vực nông nghiệp thông minh. Hệ thống được thiết kế nhằm theo dõi các thông số môi trường và chất lượng nước quan trọng trong ao nuôi như nồng độ oxy hòa tan (O₂), độ pH, nồng độ amoniac (NH₃), nhiệt độ nước, mực nước, độ đục và tổng chất rắn hòa tan trong nước (TDS). Dựa trên các dữ liệu thu thập được, hệ thống có khả năng đưa ra các quyết định điều khiển tự động nhằm duy trì môi trường sống ổn định cho thủy sản. 

Trong dự án này, vi điều khiển ESP32 đóng vai trò trung tâm, thực hiện việc thu thập dữ liệu từ các cảm biến, xử lý và điều khiển các thiết bị ngoại vi như hệ thống sục khí, bơm cấp/xả nước và cơ chế cho ăn tự động. Ngoài ra, hệ thống còn hỗ trợ giao diện giám sát thông qua web dashboard, cho phép người dùng theo dõi dữ liệu thời gian thực, nhận cảnh báo và điều khiển thiết bị từ xa. 

Hệ thống được xây dựng với mục tiêu tự động hóa quá trình giám sát và điều chỉnh môi trường, giúp giảm thiểu sự can thiệp thủ công và nâng cao hiệu quả trong nuôi trồng thủy sản. 

## **1.2. Các chức năng chính** 

Hệ thống được xây dựng với các chức năng chính như sau: 

## **Giám sát môi trường và chất lượng nước** 

- Thu thập dữ liệu từ các cảm biến: 

   - + Nồng độ O₂ (giả lập bằng biến trở) 

   - + Độ pH của nước (giả lập) 

   - + Nồng độ NH₃ (giả lập) 

   - + Nhiệt độ nước (DS18B20) 

   - + Mực nước (HC-SR04) 

   - + Tổng chất rắn hòa tan TDS 

   - + Độ đục của nước (TS-300B) 

- Dữ liệu được cập nhật liên tục và hiển thị trên giao diện giám sát. 

## **Điều khiển thiết bị** 

- 

- Điều khiển các thiết bị thông qua vi điều khiển: 

   - + Máy bơm sục khí (tăng oxy) 

   - + Máy bơm xả nước và cấp nước 

   - + Hệ thống cho ăn 

7 

- Cho phép bật/tắt thiết bị thủ công từ giao diện. 

- **Điều khiển tự động** 

   - Hệ thống tự động đưa ra quyết định điều khiển dựa trên ngưỡng: 

      - + Khi O₂ thấp → kích hoạt hệ thống sục khí 

      - + Khi NH₃ cao → kích hoạt quá trình thay nước 

      - + Khi mực nước quá thấp → kích hoạt cấp nước 

## **Cảnh báo hệ thống** 

- Phát hiện và cảnh báo khi: 

   - + Nồng độ O₂ xuống thấp 

   - + NH₃ vượt mức an toàn 

   - + pH không nằm trong khoảng cho phép 

   - + Mực nước quá cao hoặc quá thấp 

   - + Độ đục tăng bất thường 

   - + TDS vượt ngưỡng cho phép 

## **Hiển thị dữ liệu** 

- 

- 

   - Hiển thị dữ liệu môi trường theo thời gian thực 

   - Biểu diễn dữ liệu dưới dạng biểu đồ 

- Hiển thị trạng thái hoạt động của thiết bị 

- Theo dõi lịch sử thay đổi thông số môi trường 

## **1.3. Mục tiêu dự án** 

Mục tiêu của dự án là xây dựng một hệ thống nhúng có khả năng giám sát và điều khiển môi trường nuôi trồng thủy sản một cách ổn định và hiệu quả. Hệ thống cần đảm bảo khả năng thu thập dữ liệu chính xác, xử lý kịp thời và điều khiển thiết bị phù hợp với điều kiện môi trường thực tế. 

Bên cạnh đó, dự án hướng tới việc xây dựng một hệ thống có tính tự động hóa cao, giúp giảm sự phụ thuộc vào con người trong quá trình vận hành. Việc tích hợp giao diện giám sát giúp người dùng dễ dàng theo dõi và quản lý hệ thống. 

Trong tương lai, hệ thống có thể được mở rộng bằng cách sử dụng các cảm biến thực tế có độ chính xác cao hơn, cải thiện thuật toán điều khiển và mở rộng quy mô để áp dụng trong các mô hình nuôi trồng lớn hơn. 

8 

## **CHƯƠNG 2: THIẾT KẾ HỆ THỐNG** 

## **2.1. Phân tích yêu cầu hệ thống** 

## **2.1.1. Yêu cầu chức năng** 

Hệ thống giám sát và điều khiển môi trường nuôi trồng thủy sản cần đáp ứng các chức năng chính nhằm hỗ trợ người dùng theo dõi chất lượng nước và điều khiển các thiết bị trong ao nuôi một cách hiệu quả. 

**Giám sát môi trường :** Hệ thống cần có khả năng thu thập và hiển thị dữ liệu từ các cảm biến môi trường theo thời gian thực. 

**Điều khiển thiết bị :** Hệ thống cần hỗ trợ điều khiển các thiết bị ngoại vi thông qua ESP32. Người dùng có thể bật/tắt thiết bị trực tiếp từ dashboard hoặc để hệ thống tự động điều khiển. 

**Điều khiển tự động :** Hệ thống cần hỗ trợ cơ chế tự động đưa ra quyết định điều khiển dựa trên các ngưỡng môi trường được thiết lập trước. 

**Hiển thị dữ liệu và biểu đồ :** Dashboard cần hỗ trợ: 

- Hiển thị dữ liệu theo thời gian thực 

- Hiển thị trạng thái hoạt động của thiết bị 

- Biểu diễn dữ liệu bằng biểu đồ 

- 

- Theo dõi lịch sử cảnh báo và trạng thái hệ thống 

**Cảnh báo hệ thống:** Hệ thống cần phát hiện và cảnh báo khi các thông số vượt ngưỡng an toàn. Cảnh báo được hiển thị trên dashboard nhằm giúp người dùng xử lý kịp thời. 

## **2.1.2. Yêu cầu phi chức năng** 

Ngoài các chức năng chính, hệ thống cần đáp ứng một số yêu cầu phi chức năng nhằm đảm bảo tính ổn định, khả năng mở rộng và tính thực tiễn của hệ thống: 

**Tính ổn định :** Hệ thống cần hoạt động liên tục và ổn định trong quá trình giám sát môi trường. ESP32 phải đảm bảo khả năng đọc dữ liệu cảm biến và điều khiển thiết bị mà không xảy ra lỗi hoặc gián đoạn trong thời gian dài. 

**Thời gian phản hồi :** Dữ liệu môi trường cần được cập nhật gần thời gian thực để người dùng có thể theo dõi kịp thời. Các lệnh điều khiển từ dashboard cần được phản hồi nhanh chóng tới thiết bị. 

**Tính mở rộng:** Hệ thống cần được thiết kế theo hướng module hóa, cho phép mở rộng thêm các cảm biến hoặc thiết bị mới trong tương lai mà không cần thay đổi toàn bộ hệ thống. 

Ví dụ: 

9 

- bổ sung cảm biến độ mặn 

- cảm biến NO₂ 

**Tính thân thiện với người dùng :** Dashboard cần được thiết kế trực quan, dễ sử dụng và hỗ trợ người dùng theo dõi trạng thái hệ thống một cách thuận tiện. 

**Khả năng kết nối :** Hệ thống cần hỗ trợ kết nối WiFi ổn định để truyền dữ liệu giữa ESP32 và web dashboard. Dữ liệu cảm biến và trạng thái thiết bị cần được đồng bộ chính xác. 

**Tính thực tiễn:** Hệ thống cần đảm bảo khả năng áp dụng cho mô hình nuôi thủy sản quy mô nhỏ và có thể nâng cấp để phù hợp với các mô hình thực tế lớn hơn trong tương lai. 

**Chi phí triển khai:** Các linh kiện sử dụng trong hệ thống cần có chi phí hợp lý, dễ tìm kiếm và phù hợp với phạm vi của một mô hình nghiên cứu và học tập. 

## **2.2. Thiết kế vật lý** 

|**2.2. Thiết kế vật lý**|**2.2. Thiết kế vật lý**|
|---|---|
|||
|**DANH SÁCH THIẾT BỊ**||
|**Tên**|**Số lượng**|
|Esp32 chip cp2102 có type c|1 cái|
|Relay 5VDC - Mạch Relay 5V 2 Kênh|1 cái|
|Đèn led  ( 1 cái giả lập cho ăn, 4 cái cho motor bơm oxy)|5 cái|
|Chiết áp đơn Biến trở xanh RK097N 15mm 3 chân đơn ( giả lập<br>cho Nh3, O2, ph)|3 cái|
|Máy bơm mini bơm chìm siêu nhỏ 3V-5V bơm mạnh và 1 cái dây<br>chuyền nước|2 cái|
|Dây cảm biến nhiệt độ DS18B20|1 cái|
|Cảm Biến Siêu Âm HC-SR04 (Đo Khoảng Cách) (để đo mực<br>nước)|1 cái|
|Mô Đun Cảm Biến Nước TDS Cho Arduino Chất Lượng Nước|1 cái|
|Mô-đun phát hiện trộn nước cảm biến độ đục (TS-300B)|1 cái|



10 

## **2.2.1. Vi điều khiển ESP32** 

## **Mô tả chức năng:** 

ESP32 là trung tâm xử lý của hệ thống, có nhiệm vụ thu thập dữ liệu từ các cảm biến như nhiệt độ, mực nước và các tín hiệu giả lập (O₂, pH, NH₃), sau đó xử lý và đưa ra quyết định điều khiển các thiết bị như relay, máy bơm và LED. Ngoài ra, ESP32 còn hỗ trợ giao tiếp với giao diện giám sát để truyền dữ liệu và nhận lệnh điều khiển từ người dùng. 

## **Thông số kỹ thuật:** 

- 

   - Vi xử lý (CPU): Tensilica Xtensa LX6 dual-core, lên đến 240 MHz 

- RAM: 520 KB SRAM 

- Flash: 4 MB (tùy phiên bản board) 

- Wi-Fi: 802.11 b/g/n (2.4 GHz) 

- Bluetooth: v4.2 BR/EDR và BLE 

- GPIO: ~30+ chân có thể lập trình 

- 

   - ADC: 12-bit, nhiều kênh (dùng để đọc biến trở) 

- PWM: hỗ trợ điều khiển thiết bị ngoại vi 

- Điện áp hoạt động: 3.3V 

- 

   - Nguồn cấp: 5V qua cổng USB Type-C 

- Chip USB-UART: CP2102 (dùng để nạp chương trình và giao tiếp máy tính) 

## **Lý do lựa chọn:** 

- 

- 

- 

- 

- 

- Hiệu năng cao, đáp ứng tốt việc xử lý dữ liệu và điều khiển thời gian thực 

- Tích hợp sẵn nhiều ngoại vi (ADC, PWM, GPIO) phù hợp cho hệ thống nhúng 

- Hỗ trợ giao tiếp không dây, thuận tiện cho việc giám sát và điều khiển từ xa Giá thành hợp lý, dễ triển khai 

- Cộng đồng sử dụng lớn, nhiều tài liệu và thư viện hỗ trợ 

. 

**Hình 2.1:** _Vi điều khiển ESP32_ 

11 

## **2.2.2. Cảm biến nhiệt độ DS18B20** 

## **Mô tả chức năng:** 

DS18B20 là cảm biến nhiệt độ dạng kỹ thuật số, được sử dụng để đo nhiệt độ nước trong hệ thống nuôi trồng thủy sản. Cảm biến cung cấp dữ liệu nhiệt độ chính xác và ổn định, giúp hệ thống theo dõi sự thay đổi nhiệt độ theo thời gian thực, từ đó đưa ra cảnh báo khi nhiệt độ vượt quá ngưỡng cho phép. 

Trong hệ thống, DS18B20 được đặt trực tiếp trong môi trường nước (dạng chống nước), đảm bảo đo được nhiệt độ thực tế của ao nuôi. 

## **Thông số kỹ thuật:** 

- Loại cảm biến: Kỹ thuật số (Digital Temperature Sensor) 

- Dải đo nhiệt độ: -55°C đến +125°C 

- Độ chính xác: ±0.5°C (trong khoảng -10°C đến +85°C) 

- Độ phân giải: 9 đến 12 bit (có thể cấu hình) 

- Giao tiếp: 1-Wire (chỉ cần 1 chân dữ liệu) 

- Điện áp hoạt động: 3.0V – 5.5V 

- Thời gian chuyển đổi: ~750 ms (ở độ phân giải 12-bit) 

## **Lý do lựa chọn:** 

- Độ chính xác cao, phù hợp đo nhiệt độ môi trường nước 

- Giao tiếp đơn giản (chỉ cần 1 chân dữ liệu) → tiết kiệm GPIO 

- - Có phiên bản chống nước, phù hợp cho môi trường ao nuôi 

- Dễ sử dụng với ESP32, có nhiều thư viện hỗ trợ 

- Giá thành thấp, dễ triển khai trong mô hình thực tế 

**Hình 2.2:** _Cảm biến DS18B20_ 

12 

## **Chân kết nối:** 

|**Chân**|**Chức năng**|**Kết nối với ESP32**|
|---|---|---|
|VCC|Nguồn cấp|3.3V|
|GND|Đường về của dòng điện|GND|
|DATA|Dữ liệu|GPIO|



## **2.2.3. LED 5mm** 

## **Mô tả chức năng:** 

- LED dùng để hiển thị trạng thái  (ví dụ: bật/tắt) 

- Minh họa cho các thiết bị khác như : Máy bơm oxy, máy cho ăn. 

## **Thông số:** 

- Loại: LED đơn sắc 

- Màu: Đỏ/Xanh/Vàng 

- Điện áp thuận: 2.0-2.2V 

- Dòng điện: 20 mA 

- Góc chiếu: 120° 

- Tuổi thọ: 50,000 giờ 

**Hình 2.3:** _LED 5mm_ 

## **2.2.4. Cảm Biến Siêu Âm HC-SR04** 

## **Mô tả chức năng:** 

Trong hệ thống nuôi trồng thủy sản, việc giám sát mực nước đóng vai trò quan trọng nhằm đảm bảo môi trường sống ổn định cho thủy sản. Để thực hiện chức năng này, hệ thống sử dụng cảm biến siêu âm HC-SR04 để đo khoảng cách từ cảm biến đến mặt nước, từ đó xác định chiều cao mực nước trong bể hoặc ao nuôi. 

13 

Cảm biến hoạt động bằng cách phát ra sóng siêu âm và tính toán thời gian sóng phản xạ trở lại khi gặp bề mặt nước. Dựa trên khoảng cách đo được, ESP32 sẽ tính toán mực nước hiện tại và đưa ra cảnh báo khi mực nước vượt quá hoặc thấp hơn ngưỡng cho phép. Ngoài ra, hệ thống có thể tự động kích hoạt bơm cấp hoặc xả nước để duy trì mức nước ổn định. 

Mặc dù trong các hệ thống thực tế người ta thường sử dụng phao cơ hoặc công tắc phao (Float Switch) để giám sát mực nước do tính ổn định và độ bền cao, cảm biến HCSR04 được lựa chọn trong mô hình này vì dễ triển khai, chi phí thấp và phù hợp cho mục đích nghiên cứu, học tập và xây dựng hệ thống thử nghiệm. 

## **Thông số kỹ thuật:** 

- Nguyên lý hoạt động: Sóng siêu âm (Ultrasonic) 

- Khoảng đo: 2 cm – 400 cm 

- Độ chính xác: ~3 mm 

- Tần số hoạt động: 40 kHz 

- Điện áp hoạt động: 5V 

- Dòng tiêu thụ: ~15 mA 

- Góc đo: ~15 độ 

## **Chân kết nối:** 

|**Chân kết nối:**|||
|---|---|---|
||||
|**Chân**|**Chức năng**|**Kết nối với ESP32**|
|VCC|Nguồn cấp|5V|
|GND|Mass|GND|
|TRIG|Phát xung|GPIO|
|ECHO|Nhận xung|GPIO|



14 

**Hình 2.4:** _Cảm Biến Siêu Âm HC-SR04_ 

## **2.2.5. Mạch Relay 5V 2 Kênh** 

## **Mô tả chức năng:** 

Mạch relay 5V 2 kênh được sử dụng để điều khiển đóng/ngắt các thiết bị điện như máy bơm nước trong hệ thống. Relay hoạt động như một công tắc điện tử, 

cho phép vi điều khiển ESP32 điều khiển các thiết bị có công suất lớn hơn thông qua tín hiệu điện áp thấp. 

Trong hệ thống, relay được sử dụng để điều khiển hai máy bơm: 

- Một máy bơm dùng để cấp nước hoặc sục khí 

- 

- Một máy bơm dùng để xả nước khi nồng độ NH₃ vượt ngưỡng 

## **Thông số kỹ thuật:** 

- Điện áp điều khiển: 5V 

- Số kênh: 2 kênh (điều khiển độc lập) 

- Dòng tải tối đa: ~10A (tùy module) 

- Điện áp tải: 250V AC hoặc 30V DC 

- Tín hiệu điều khiển: Digital (HIGH/LOW) 

- Có optocoupler cách ly (tùy module) 

## **Chân kết nối:** 

|**Chân Chức năng**|**Chân Chức năng**|**Kết nối với ESP32**|
|---|---|---|
|VCC Nguồn|VCC Nguồn|5V|



15 

|GND Mass|GND Mass||GND|
|---|---|---|---|
|IN1|Điều khiển relay 1|Điều khiển relay 1|GPIO|
|IN2|Điều khiển relay 2|Điều khiển relay 2|GPIO|



**Hình 2.5:** _Mạch Relay 5V 2 Kênh_ 

## **2.2.6. Chiết áp đơn** 

## **Mô tả chức năng:** 

Chiết áp (biến trở) được sử dụng để giả lập các cảm biến môi trường trong hệ thống, bao gồm nồng độ oxy hòa tan (O₂), độ pH và nồng độ amoniac (NH₃). Khi người dùng xoay núm chiết áp, điện áp đầu ra sẽ thay đổi tương ứng, từ đó ESP32 đọc giá trị analog và chuyển đổi thành các giá trị môi trường giả lập. 

Việc sử dụng chiết áp giúp mô phỏng sự thay đổi của các thông số môi trường một cách linh hoạt, phục vụ cho việc kiểm thử và trình diễn hệ thống mà không cần sử dụng cảm biến thực tế. 

## **Thông số kỹ thuật:** 

- Loại: Biến trở xoay (Rotary Potentiometer) 

- Số chân: 3 chân 

- Giá trị điện trở: thường 10kΩ (tùy loại) 

- Kiểu tín hiệu: Analog 

- Điện áp hoạt động: 0 – 3.3V (khi dùng với ESP32) 

## **Chân kết nối:** 

16 

|**Chân**|**Chân**|**Chức năng**|**Kết nối**|
|---|---|---|---|
|Chân 1|Chân 1|Nguồn|3.3V|
|Chân 2|Chân 2|Tín hiệu (OUT)|GPIO ADC|
|Chân 3|Chân 3|Mass (GND)|GND|



**Hình 2.6:** _Chiết áp đơn_ 

## **2.2.7. Breadboard và dây nối** 

Breadboard là một loại bảng mạch không hàn được sử dụng rộng rãi trong điện tử và kỹ thuật điện để xây dựng và kiểm tra các mạch điện một cách nhanh chóng và dễ dàng. Nó cho phép kết nối các linh kiện điện tử như ESP32, cảm biến, LED,... mà không cần hàn, giúp thay đổi và sửa đổi mạch dễ dàng hơn trong giai đoạn thử nghiệm. 

Thông số: 

- Loại: 830 holes 

- Kích thước: 165mm x 55mm 

- Điểm kết nối: 830 điểm 

- Rails nguồn: 2 dãi (+ và -) 

**Hình 2.7:** _Breadboard_ 

17 

Dây nối dùng để kết nối ESP32 với các thiết bị ngoại vi như cảm biến, LED, micro và quạt, giúp việc lắp ráp. 

Thông số: 

- Loại: Jumper wires 

- Đầu: Male-to-Male, Male-to-Female 

- Màu sắc: Phân biệt theo chức năng 

   - + Đỏ: VCC/3.3V 

   - + Đen: GND 

   - + Khác: Signal 

**Hình 2.8:** _Dây nối_ 

## **2.2.8. Ống nước** 

## **Mô tả chức năng:** 

Ống dẫn nước mini được sử dụng để dẫn nước giữa các thành phần trong hệ thống như máy bơm, bể chứa và đầu ra. Trong mô hình, ống nước đóng vai trò vận chuyển nước khi hệ thống thực hiện các chức năng như cấp nước, xả nước. 

Ống dẫn nước giúp mô phỏng dòng chảy thực tế trong ao nuôi, đảm bảo hệ thống hoạt động đúng với nguyên lý của một hệ thống nuôi trồng thủy sản. 

## **Thông số kỹ thuật:** 

- Chất liệu: Nhựa PVC mềm hoặc silicone 

- Đường kính trong: ~4 – 8 mm (tùy loại máy bơm) 

- Chiều dài: Tùy thuộc vào mô hình 

- Đặc tính: Mềm, dễ uốn, chống rò rỉ nước 

18 

**Hình 2.9:** _Ống nước_ 

## **2.2.9. Máy bơm** 

## **Mô tả chức năng:** 

Máy bơm mini là thiết bị được sử dụng để điều khiển dòng nước trong hệ thống, bao gồm việc cấp nước và xả nước. Trong mô hình, máy bơm đóng vai trò quan trọng trong việc thực hiện các hành động điều khiển tự động dựa trên điều kiện môi trường. 

Cụ thể: 

- Một máy bơm dùng để xả nước khi nồng độ NH₃ cao 

- Một máy bơm dùng để cấp nước mới hoặc hỗ trợ tuần hoàn nước 

Máy bơm được điều khiển thông qua mạch relay, cho phép ESP32 bật/tắt theo logic đã lập trình. 

## **Chân kết nối:** 

|**Chân**<br>**Chức năng**|**Kết nối**|
|---|---|
|Dây đỏ (+) Nguồn dương Nối với relay (chân NO/COM)|Dây đỏ (+) Nguồn dương Nối với relay (chân NO/COM)|
|Dây đen (-) Mass (GND)|Nối GND nguồn|



19 

**Hình 2.10:** _Máy bơm_ 

## **2.2.10. Cảm biến chất lượng nước TDS** 

## **Mô tả chức năng:** 

Mô đun cảm biến TDS (Total Dissolved Solids) được sử dụng để đo tổng lượng chất rắn hòa tan trong nước, từ đó đánh giá chất lượng nước trong hệ thống nuôi trồng thủy sản. Giá trị TDS phản ánh mức độ tồn tại của các ion và khoáng chất hòa tan như muối, kim loại và các tạp chất khác trong nước. 

Trong hệ thống, cảm biến TDS giúp theo dõi sự thay đổi chất lượng nước theo thời gian thực, hỗ trợ phát hiện tình trạng ô nhiễm hoặc nồng độ chất hòa tan vượt quá mức cho phép. Dữ liệu thu được sẽ được ESP32 xử lý để đưa ra cảnh báo hoặc kích hoạt hệ thống cấp/xả nước tự động nhằm duy trì môi trường sống ổn định cho thủy sản. 

Cảm biến được đặt trực tiếp trong môi trường nước để đo liên tục và gửi dữ liệu về bộ điều khiển trung tâm. 

## **Thông số kỹ thuật:** 

- Loại cảm biến: Cảm biến TDS analog 

- Dải đo TDS: 0 – 1000 ppm (phụ thuộc chất lượng nước) 

- Điện áp hoạt động: 3.3V – 5.5V 

- Tín hiệu đầu ra: Analog 

- Giao tiếp với vi điều khiển: ADC (Analog to Digital Converter) 

- Nhiệt độ hoạt động: 0°C – 80°C 

- Thời gian phản hồi: < 500 ms 

- 

- Độ chính xác: ±10% F.S (Full Scale) 

## **Lý do lựa chọn:** 

- Giúp đánh giá nhanh chất lượng nước trong ao nuôi 

- - Dễ dàng kết nối với ESP32 thông qua chân ADC 

20 

- Kích thước nhỏ gọn, dễ lắp đặt trong mô hình thực tế 

- Giá thành thấp, phù hợp cho hệ thống IoT nông nghiệp 

- Có thư viện và tài liệu hỗ trợ phong phú 

- Hoạt động ổn định trong môi trường nước liên tục 

## **Chân kết nối:** 

|**Chân**|**Chức năng**|**Kết nối với ESP32**|
|---|---|---|
|VCC|Nguồn cấp|3.3V|
|GND|Đường về của dòng điện|GND|
|AOUT|Tín hiệu analog đầu ra|GPIO (ADC)|



**Hình 2.11:** _Cảm biến chất lượng nước TDS_ 

## **2.2.11. Cảm biến độ đục của nước (TS-300B)** 

## **Mô tả chức năng:** 

Mô đun cảm biến độ đục của nước TS-300B được sử dụng để phát hiện mức độ sạch hoặc ô nhiễm của nước trong hệ thống nuôi trồng thủy sản. Cảm biến hoạt động dựa trên nguyên lý đo độ dẫn điện của nước để đánh giá chất lượng môi trường nước theo thời gian thực. 

Trong hệ thống, TS-300B giúp theo dõi sự thay đổi chất lượng nước nhằm phát hiện sớm các dấu hiệu ô nhiễm hoặc sự tích tụ của các chất có hại. Khi giá trị đo vượt quá ngưỡng cho phép, ESP32 sẽ đưa ra cảnh báo hoặc kích hoạt hệ thống thay nước nhằm đảm bảo môi trường sống ổn định cho thủy sản. 

21 

Cảm biến được đặt trực tiếp trong nước để thực hiện việc giám sát liên tục và truyền dữ liệu về bộ điều khiển trung tâm. 

## **Thông số kỹ thuật:** 

- Loại cảm biến: Cảm biến chất lượng nước analog 

- Điện áp hoạt động: 3.3V – 5V 

- Tín hiệu đầu ra: Analog và Digital 

- Giao tiếp với vi điều khiển: ADC / Digital IO 

- Khả năng phát hiện: Mức độ ô nhiễm và độ dẫn điện của nước 

- Nhiệt độ hoạt động: 0°C – 80°C 

- Thời gian phản hồi: Nhanh, theo thời gian thực 

- Kích thước nhỏ gọn, dễ tích hợp vào hệ thống IoT 

## **Lý do lựa chọn:** 

- Có khả năng giám sát chất lượng nước liên tục 

- Hỗ trợ cả tín hiệu Analog và Digital, thuận tiện cho việc xử lý dữ liệu 

- Dễ dàng kết nối với ESP32 

- Chi phí thấp, phù hợp cho mô hình nghiên cứu và thực tế 

- Kích thước nhỏ gọn, dễ lắp đặt trong môi trường ao nuôi 

- Hỗ trợ phát hiện sớm các thay đổi bất thường của môi trường nước 

## **Chân kết nối:** 

|**Chân**|**Chức năng**|**Kết nối với ESP32**|
|---|---|---|
|VCC|Nguồn cấp|3.3V|
|GND|Đường về của dòng điện|GND|
|AO|Tín hiệu analog đầu ra|GPIO (ADC)|
|DO|Tín hiệu digital đầu ra|GPIO Digital|



**Hình 2.12:** _Cảm biến độ đục của nước (TS-300B)_ 

22 

## **2.2.12. Thiết kế mạch** 

**Hình 2.13:** _Sơ đồ nối dây thiết kế_ 

**Hình 2.14:** _Minh họa thực tế_ 

23 

## **2.3. Các giao thức truyền thông** 

## **2.3.1. MQTT** 

MQTT là giao thức truyền thông nhẹ, phù hợp với các hệ thống nhúng có tài nguyên hạn chế và yêu cầu truyền dữ liệu nhanh, ổn định. Giao thức này hoạt động theo mô hình Publish/Subscribe, trong đó các thiết bị trao đổi dữ liệu thông qua một máy chủ trung gian gọi là MQTT Broker. 

Trong hệ thống giám sát và điều khiển môi trường nuôi trồng thủy sản, MQTT được sử dụng để truyền dữ liệu giữa vi điều khiển ESP32 và hệ thống giám sát. 

Cụ thể trong hệ thống: 

- ESP32 thu thập dữ liệu từ các cảm biến (nhiệt độ, mực nước) và các giá trị giả lập (O₂, pH, NH₃,..), sau đó **publish dữ liệu** lên MQTT Broker theo các topic đã định nghĩa. 

- Web dashboard hoặc server sẽ **subscribe các topic này** để nhận dữ liệu theo thời gian thực và hiển thị cho người dùng dưới dạng số liệu và biểu đồ. 

- Khi người dùng thực hiện thao tác điều khiển trên dashboard (như bật/tắt máy bơm oxy, xả nước, cho ăn), lệnh điều khiển sẽ được **publish lên MQTT Broker** theo các topic . 

- ESP32 sẽ **subscribe các topic điều khiển** , nhận lệnh và thực hiện hành động tương ứng (bật relay, bật LED, điều khiển máy bơm). 

Nhờ cơ chế này, hệ thống đảm bảo việc truyền dữ liệu hai chiều nhanh chóng, ổn định và tiết kiệm băng thông. 

## **2.3.2. HTTP** 

HTTP là giao thức truyền tải siêu văn bản hoạt động ở lớp ứng dụng trong mô hình TCP/IP. Giao này thức hoạt động theo mô hình Request/Response, trong đó client gửi yêu cầu (request) đến server, và server phản hồi (response) lại bằng dữ liệu hoặc kết quả xử lý tương ứng. 

HTTP nổi bật với tính đơn giản được thiết kế dễ hiểu, dễ đọc, giúp cho việc phát triển, kiểm thử thuận tiện và hỗ trợ nhiều phương thức như GET, POST, PUT, DELETE cho các hành động khác nhau trên tài nguyên. HTTP cũng có khả năng mở rộng, với việc sử dụng những header HTTP, giao thức này trở nên linh hoạt hơn và dễ dàng thêm các chức năng mới. 

Trong hệ thống giám sát và điều khiển môi trường tự động cho mô hình nuôi trồng thủy sản , HTTP đảm nhận vai trò giao tiếp giữa người dùng và máy chủ trung tâm, thay vì giao tiếp trực tiếp với thiết bị phần cứng như ESP32. 

Với các đặc điểm trên, HTTP được ứng dụng trong hệ thống như sau: 

24 

- Người dùng truy cập web dashboard thông qua trình duyệt để giám sát các thông số môi trường và trạng thái thiết bị. 

- Khi người dùng thực hiện thao tác điều khiển (bật/tắt máy bơm, cho ăn,…), yêu cầu sẽ được gửi từ client lên server thông qua HTTP. 

- Server xử lý yêu cầu, lưu trữ thông tin (nếu cần), sau đó chuyển tiếp lệnh điều khiển đến ESP32 thông qua MQTT Broker. 

- Ngoài ra, HTTP còn được sử dụng để: 

   - + Truy xuất dữ liệu lịch sử 

   - + Hiển thị biểu đồ thống kê 

   - + Cung cấp API phục vụ giao diện dashboard 

## **2.4. Thiết kế phần mềm** 

## **2.4.1. Kiến trúc tổng quan** 

**Hình 2.15:** _Kiến trúc tổng quan_ 

## **2.4.2. Công nghệ sử dụng** 

- _a. Frontend_ 

Công nghệ sử dụng: ReactJS 

25 

ReactJS là một thư viện JavaScript mã nguồn mở, mạnh mẽ và phổ biến được phát triển bởi Facebook, dùng để xây dựng giao diện người dùng (UI) một cách linh hoạt và hiệu quả. 

Vai trò trong dự án: 

- Tạo ra các trang web động, có tính tương tác cao cho người dùng. 

- Hiển thị dữ liệu nhận được từ Back-end một cách trực quan (thông qua biểu đồ, bảng, ...). 

- Gửi các yêu cầu (request) HTTP đến Back-end để lấy, thêm, sửa, xóa dữ liệu. 

Lý do lựa chọn: 

- Hiệu suất cao: Sử dụng Virtual DOM để tối ưu hóa việc cập nhật giao diện. 

- Cộng đồng lớn: Hệ sinh thái phong phú với nhiều thư viện hỗ trợ (UI components, routing, state management). 

- Dễ bảo trì: Cấu trúc component giúp code dễ đọc, dễ tái sử dụng và bảo trì. 

- Học tập nhanh: Cú pháp rõ ràng, tài liệu đầy đủ. 

## _**b.** Backend_ 

Công nghệ sử dụng: FastAPI, ngôn ngữ lập trình Python, mô hình Whisper 

FastAPI là một framework hiện đại dùng Python để xây dựng các API, tối ưu cho hiệu năng cao, hỗ trợ kiểu dữ liệu và tự động sinh tài liệu API (OpenAPI/Swagger). 

Vai trò trong dự án: 

- Xây dựng các API (RESTful API) để Front-end có thể giao tiếp và lấy dữ liệu. 

- Xử lý logic nghiệp vụ, xác thực người dùng và phân quyền. 

- Tiếp nhận dữ liệu từ phần cứng (ESP32) thông qua giao thức MQTT. 

- Tương tác với cơ sở dữ liệu MySQL để lưu trữ và truy vấn dữ liệu. 

ORM sử dụng SQLAlchemy. SQLAlchemy là một ORM mạnh mẽ cho Python, hỗ trợ tương tác an toàn với cơ sở dữ liệu mà không cần viết trực tiếp các câu truy vấn SQL. Vai trò trong dự án: 

- Thay thế việc viết các câu truy vấn SQL thuần bằng API trực quan và an toàn. 

- Đảm bảo an toàn kiểu dữ liệu khi tương tác với cơ sở dữ liệu, giảm thiểu lỗi. 

- Quản lý lược đồ cơ sở dữ liệu (schema) dễ dàng và có thể version control. 

26 

- Tăng năng suất phát triển và giúp code back-end sạch sẽ, dễ bảo trì hơn. 

## _c. Hardware_ 

Phần cứng bao gồm các thiết bị đã được mô tả trong mục _Thiết kế vật lý_ , trong đó ESP32 đóng vai trò là vi điều khiển trung tâm, điều phối và xử lý dữ liệu từ các cảm biến cũng như điều khiển các thiết bị ngoại vi. ESP32 giao tiếp với hệ thống back-end thông qua các giao thức MQTT và HTTP, đảm bảo truyền nhận dữ liệu ổn định và hiệu quả. 

## _d. Database_ 

Hệ thống sử dụng MySQL làm hệ quản trị cơ sở dữ liệu. 

MySQL là hệ quản trị cơ sở dữ liệu quan hệ (RDBMS) mã nguồn mở, cho phép lưu trữ và quản lý dữ liệu theo các bảng có quan hệ với nhau bằng ngôn ngữ SQL. MySQL nổi bật với tính ổn định, hiệu suất cao, bảo mật tốt và khả năng mở rộng, đồng thời tích hợp dễ dàng với nhiều ngôn ngữ lập trình và hệ điều hành. 

Vai trò trong dự án: 

- Lưu trữ dữ liệu có cấu trúc của ứng dụng, lịch sử dữ liệu cảm biến, lịch sử bật tắt thiết bị. 

- Cung cấp dữ liệu cho Back-end khi Front-end gửi yêu cầu thông qua API. 

- Backend kết nối và thao tác với cơ sở dữ liệu MySQL hiệu quả bằng ORM SQLAlchemy. 

27 

## **2.5. Thiết kế logic** 

## **2.5.1. Biểu đồ use case toàn hệ thống** 

**Hình 2.16:** _Biểu đồ use case_ 

- **Điều khiển thiết bị qua Web Dashboard:** Use Case này cho phép người dùng bật/tắt và điều khiển các thiết bị trong hệ thống như hệ thống sục khí, bơm cấp/xả nước và hệ thống cho ăn thông qua giao diện web dashboard theo thời gian thực. 

- **Xem dữ liệu cảm biến:** Use Case này cho phép người dùng theo dõi các thông số môi trường nuôi trồng thủy sản như O₂, pH, NH₃, nhiệt độ nước, mực nước, TDS và độ đục được cập nhật liên tục từ hệ thống cảm biến. 

- **Xem lịch sử hoạt động thiết bị:** Use Case này cho phép người dùng xem lại lịch sử hoạt động của các thiết bị và các sự kiện trong hệ thống như thời điểm bật/tắt bơm, kích hoạt sục khí hoặc phát sinh cảnh báo môi trường. 

- **Quản lý thiết bị:** Use Case này cho phép người dùng cấu hình chế độ hoạt động của thiết bị, lựa chọn giữa chế độ tự động và điều khiển thủ công, đồng thời thiết lập các ngưỡng môi trường để hệ thống tự động thực hiện các hành động điều khiển phù hợp. 

28 

## **2.5.2. Thiết kế chi tiết** 

- _a. Chức năng Nhận và lưu dữ liệu cảm biến_ 

**Hình 2.17:** _Biểu đồ tuần tự của chức năng nhận và lưu liệu cảm biến_ 

## **Kịch bản** 

1. Thiết bị ESP32 publish dữ liệu cảm biến lên MQTT Broker theo topic tương ứng. 

2. MQTT Broker nhận và chuyển tiếp message đến MQTT Client ở phía backend. 

3. MQTT Client nhận message qua callback, sau đó phân tích topic để xác định thiết bị và loại cảm biến. 

4. MQTT Client phân tích nội dung message để lấy giá trị đo và đơn vị. 

5. Hệ thống chuyển xử lý dữ liệu sang luồng bất đồng bộ. 

6. Sensor Service xử lý và lưu trữ dữ liệu cảm biến vào cơ sở dữ liệu. 

7. Hệ thống cập nhật thời gian hoạt động gần nhất (last_seen) của thiết bị. 

8. Transaction được commit để hoàn tất việc lưu dữ liệu. 

9. Hệ thống ghi log xác nhận đã lưu thành công dữ liệu cảm biến. 

29 

## _b. Chức năng Điều khiển thiết bị_ 

**Hình 2.18:** _Biều đồ tuần tự cho chức năng điều khiển thiết bị_ 

## **Kịch bản** 

1. Người dùng gửi POST /devices/PUMP_OXY_01/control với action = "ON" từ Dashboard. 

2. FastAPI nhận request và chuyển cho Device Service xử lý. 

3. Device Service truy vấn database để lấy thông tin thiết bị theo device_id. 

4. Database trả về thông tin Device object (thiết bị tồn tại). 

5. Device Service publish lệnh điều khiển lên MQTT topic control/PUMP_OXY_01 với action "ON". 

6. MQTT Client gửi message đến MQTT Broker (Mosquitto). 

7. MQTT Broker forward message đến thiết bị ESP32. 

8. Thiết bị ESP32 nhận lệnh và thực thi (Bật máy bơm). 

9. Device Service cập nhật trạng thái thiết bị trong database thành "ON". 

10. Device Service ghi log lịch sử điều khiển vào bảng device_history với status "success". 

11. Database commit transaction. 

12. FastAPI trả về response 200 OK cho người dùng với thông tin thành công. 

30 

## **2.5.3. Thiết kế cơ sở dữ liệu** 

**Hình 2.19:** _Cơ sở dữ liệu hệ thống_ 

##  **Bảng devices** 

Bảng devices là bảng trung tâm của toàn bộ hệ thống, chịu trách nhiệm lưu trữ thông tin của tất cả các thiết bị IoT đang hoạt động. Mỗi thiết bị, bao gồm các node cảm biến như ESP32 hoặc các thiết bị điều khiển như máy bơm, máy cho ăn, đều được quản lý tại đây. Bảng này không chỉ lưu các thông tin cơ bản như tên, loại thiết bị hay vị trí, mà còn phản ánh trạng thái hiện tại và thời điểm hoạt động gần nhất của thiết bị. Nhờ đó, hệ thống có thể theo dõi tình trạng online/offline và phục vụ việc điều khiển thiết bị một cách hiệu quả. 

|**Tên cột**|**Kiểu dữ liệu**|**Ràng buộc**|**Ý nghĩa**|
|---|---|---|---|
|id|BIGINT|PK, AUTO_INCREMENT|Khóa chính nội bộ của bảng,<br>dùng để định danh duy nhất|



31 

||||mỗi thiết bị trong database<br>và tối ưu join|
|---|---|---|---|
|device_id|VARCHAR(50)|NOT NULL, UNIQUE|Định danh nghiệp vụ của<br>thiết bị (do firmware khai<br>báo), dùng trong MQTT và<br>API|
|name|VARCHAR(100)|NOT NULL|Tên hiển thị của thiết bị,<br>giúp người dùng dễ nhận<br>biết|
|type|ENUM|NOT NULL|Loại thiết bị (esp32, pump,<br>feeder, relay), giúp phân loại<br>và xử lý logic|
|status|ENUM|DEFAULT ‘OFF’|Trạng thái hiện tại của thiết<br>bị (ON/OFF)|
|location|VARCHAR(100)|NULL|Vị trí vật lý của thiết bị trong<br>hệ thống|
|last_seen|TIMESTAMP|NULL|Thời điểm thiết bị gửi dữ<br>liệu lần cuối, dùng để phát<br>hiện thiết bị offline|
|created_at|TIMESTAMP|DEFAULT<br>CURRENT_TIMESTAMP|Thời điểm thiết bị được<br>thêm vào hệ thống|
|updated_at|TIMESTAMP|AUTO UPDATE|Thời điểm cập nhật gần nhất<br>của bản ghi|



##  **Bảng sensor_data** 

Bảng sensor_data được sử dụng để lưu trữ toàn bộ dữ liệu đo lường từ các cảm biến trong hệ thống theo thời gian. Đây là bảng có khối lượng dữ liệu lớn nhất do các thiết bị gửi dữ liệu liên tục với tần suất cao. Mỗi bản ghi trong bảng tương ứng với một giá trị đo 

32 

của một chỉ số cụ thể tại một thời điểm xác định, ví dụ như nhiệt độ, độ pH hay nồng độ oxy. Thiết kế này giúp hệ thống dễ dàng thực hiện các truy vấn phân tích theo thời gian, phục vụ cho việc giám sát môi trường và hiển thị biểu đồ trên dashboard. 

|||||
|---|---|---|---|
|**Tên cột**|**Kiểu dữ liệu**|**Ràng buộc**|**Ý nghĩa**|
|id|BIGINT|PK, AUTO_INCREMENT|Khóa chính, định danh<br>duy nhất mỗi bản ghi<br>dữ liệu cảm biến|
|device_id|VARCHAR(50)|FK, NOT NULL|Tham chiếu đến thiết<br>bị gửi dữ liệu (liên kết<br>với bảng devices)|
|metric_type|VARCHAR(50)|NOT NULL|Loại chỉ số đo<br>(temperature, ph,<br>o2,…)|
|value|FLOAT|NOT NULL|Giá trị số đo được từ<br>cảm biến|
|unit|VARCHAR(20)|NULL|Đơn vị của giá trị đo<br>(°C, mg/L,…)|
|created_at|TIMESTAMP|DEFAULT<br>CURRENT_TIMESTAMP|Thời điểm dữ liệu<br>được ghi nhận|



##  **Bảng device_history** 

Bảng device_history đóng vai trò ghi lại toàn bộ lịch sử các hành động điều khiển thiết bị trong hệ thống. Mỗi khi có một lệnh được gửi đến thiết bị là từ người dùng, từ API hay từ hệ thống tự động, một bản ghi sẽ được thêm vào bảng này. Nhờ đó, hệ thống có thể theo dõi được những thao tác đã thực hiện, kết quả của từng lệnh (thành công hay thất bại), cũng như nguồn phát sinh lệnh. Đây là thành phần quan trọng giúp đảm bảo khả năng truy vết (audit) và hỗ trợ kiểm tra, debug khi xảy ra sự cố. 

33 

|||||
|---|---|---|---|
|**Tên cột**|**Kiểu dữ liệu**|**Ràng buộc**|**Ý nghĩa**|
|id|BIGINT|PK, AUTO_INCREMENT|Khóa chính, định danh mỗi<br>hành động trong lịch sử|
|device_id|VARCHAR(50)|FK, NOT NULL|Thiết bị nhận lệnh điều<br>khiển|
|action|ENUM|NOT NULL|Loại hành động (ON, OFF,<br>FEED, RESET,…)|
|status|ENUM|NOT NULL|Kết quả thực hiện (success /<br>failed)|
|source|ENUM|NOT NULL|Nguồn phát sinh lệnh<br>(manual, api, schedule)|
|note|TEXT|NULL|Ghi chú chi tiết, thường<br>dùng để lưu lỗi hoặc mô tả|
|created_at|TIMESTAMP|DEFAULT<br>CURRENT_TIMESTAMP|Thời điểm hành động được<br>thực hiện|



34 

## **CHƯƠNG 3: XÂY DỰNG AI SERVICE** 

## **3.1. Giới thiệu bài toán** 

Trong hệ thống giám sát chất lượng nước, các cảm biến IoT liên tục thu thập dữ liệu theo thời gian thực và gửi về hệ thống xử lý trung tâm. Các chỉ số được ghi nhận bao gồm độ pH của nước, tổng lượng chất rắn hòa tan (TDS) và nhiệt độ nước. 

Tuy nhiên, việc chỉ hiển thị dữ liệu hiện tại chưa đủ để hỗ trợ người dùng đưa ra quyết định trong các tình huống thực tế. Hệ thống cần có khả năng phân tích xu hướng thay đổi của các chỉ số và dự đoán giá trị trong tương lai để cảnh báo sớm khi chất lượng nước có dấu hiệu bất thường. 

Trong đề tài này, mô hình LSTM được sử dụng để học mối quan hệ giữa các dữ liệu lịch sử và dự đoán các giá trị chất lượng nước tại thời điểm tiếp theo. 

Mục tiêu của hệ thống AI: 

- Dự đoán giá trị pH trong tương lai 

- Dự đoán giá trị TDS trong tương lai 

- Dự đoán nhiệt độ nước trong tương lai 

- Hỗ trợ hệ thống cảnh báo sớm 

Ví dụ: 

Bảng dữ liệu đầu vào: 

|||||
|---|---|---|---|
|**Thời gian**|**pH**|**TDS**|**Nhiệt độ**|
|10:00|7.2|310|24.5|
|10:05|7.1|315|24.8|
|10:10|7.0|320|25|



Sau khi mô hình học: 

|Sau khi mô hình học:||||
|---|---|---|---|
|||||
|**Thời gian dự đoán**|**pH**|**TDS**|**Nhiệt độ**|
|10:15|6.9|324|25.2|



35 

## **3.2. Phân tích dữ liệu đầu vào** 

- - Nguồn dữ liệu: https://www.kaggle.com/datasets/bobsis/small aquaculture fishpond 

## **3.2.1. Cấu trúc bộ dữ liệu** 

Dữ liệu được lưu dưới dạng chuỗi thời gian (Time Series Data). Mỗi dòng dữ liệu thể hiện trạng thái chất lượng nước tại một thời điểm cụ thể. 

Bảng cấu trúc dữ liệu: 

|**Thuộc tính**|**Ý nghĩa**|**Kiểu dữ liệu**|
|---|---|---|
|id|Mã định danh dữ liệu|Integer|
|created_date|Thời gian ghi nhận|Datetime|
|water_pH|Độ pH của nước|Float|
|TDS|Tổng lượng chất rắn hòa tan|Float|
|water_temp|Nhiệt độ nước|Float|



Ví dụ dữ liệu: 

||||||
|---|---|---|---|---|
|**id**|**created_date**|**water_pH**|**TDS**|**water_temp**|
|1|2026-04-01 10:00:00|7.2|310|24.5|
|2|2026-04-01 10:05:00|7.1|315|24.8|
|3|2026-04-01 10:10:00|7.0|320|25|



## **3.2.2. Ý nghĩa các chỉ số nước** 

## _a. pH là chỉ số phản ánh độ axit hoặc độ bazơ của nước._ 

- pH < 7: nước có tính axit 

- pH = 7: trung tính 

- pH > 7: nước có tính bazơ 

36 

Giá trị pH phù hợp cho nước sinh hoạt thường nằm trong khoảng: 6.5–8.5 

_b. TDS (Total Dissolved Solids) là tổng lượng chất rắn hòa tan trong nước._ 

TDS bao gồm: 

- Khoáng chất 

- Muối 

- Kim loại 

- Tạp chất hữu cơ 

TDS quá cao có thể ảnh hưởng đến chất lượng nước. 

- _c. Nhiệt độ nước ảnh hưởng đến:_ 

   - Khả năng hòa tan oxy 

   - Tốc độ phản ứng hóa học 

   - hoạt động của vi sinh vật 

## **3.3. Tiền xử lý dữ liệu** 

Dữ liệu thu thập từ cảm biến thường chứa: 

- Dữ liệu bị thiếu 

- Nhiễu 

- Dữ liệu bất thường 

- Dữ liệu chưa sắp xếp theo thời gian 

Do đó cần tiến hành tiền xử lý trước khi đưa vào mô hình. 

## **3.3.1. Làm sạch dữ liệu** 

Các bước thực hiện: 

- Xóa giá trị rỗng 

- Sắp xếp dữ liệu theo thời gian 

- Loại bỏ dữ liệu bất thường 

Ví dụ: 

- pH <0 

- pH >14 

- nhiệt độ âm 

- TDS quá lớn 

## **3.3.2. Chuẩn hóa dữ liệu** 

Do các đặc trưng có đơn vị khác nhau: 

Ví dụ: 

37 

- pH: 6–8 

- TDS: 300–500 

- nhiệt độ: 24–30 

Nếu không chuẩn hóa, mô hình sẽ ưu tiên đặc trưng có giá trị lớn hơn. 

Phương pháp sử dụng: 

## **Min-Max Normalization (Min-Max Scaling)** 

Công thức: 

**==> picture [124 x 31] intentionally omitted <==**

Giải thích: 

- X: giá trị dữ liệu ban đầu 

- 𝑋𝑚𝑖𝑛: giá trị nhỏ nhất trong tập dữ liệu 

- 𝑋𝑚𝑎𝑥: giá trị lớn nhất trong tập dữ liệu 

- 𝑋𝑠𝑐𝑎𝑙𝑒𝑑: giá trị sau khi chuẩn hóa 

Phương pháp Min-Max Scaling được sử dụng để chuẩn hóa dữ liệu về cùng một khoảng giá trị, thường là từ 0 đến 1. Việc chuẩn hóa giúp giảm sự chênh lệch về đơn vị đo giữa các đặc trưng và cải thiện hiệu quả huấn luyện của mô hình LSTM. 

Sau khi chuẩn hóa: 

|Sau khi chuẩn hóa:|||
|---|---|---|
||||
|**pH**|**TDS**|**Temp**|
|0.65|0.32|0.40|
|0.61|0.38|0.43|



## **3.3.3. Tạo dữ liệu chuỗi thời gian** 

LSTM không sử dụng từng điểm riêng lẻ mà sử dụng một chuỗi dữ liệu liên tiếp. 

Ví dụ: 

Giả sử: 

window_size=5 

Dữ liệu: 

38 

||||
|---|---|---|
|**pH**|**TDS**|**Temp**|
|7.2|310|24.5|
|7.1|315|24.8|
|7.0|320|25|
|6.9|323|25.1|
|6.8|325|25.2|
|6.7|327|25.4|



## **Input:** 

[ 

[7.2,310,24.5], [7.1,315,24.8], [7.0,320,25], [6.9,323,25.1], [6.8,325,25.2] 

] 

## **Output:** 

[6.7,327,25.4] 

## **3.4. Giới thiệu mô hình LSTM** 

## **3.4.1. Tổng quan về mô hình LSTM** 

Mô hình LSTM (Long Short-Term Memory) là một dạng đặc biệt của mạng nơ-ron hồi tiếp (Recurrent Neural Network - RNN), được thiết kế nhằm giải quyết hạn chế của RNN truyền thống trong việc học các mối quan hệ phụ thuộc dài hạn trong dữ liệu chuỗi thời gian. 

RNN thông thường có khả năng lưu trữ thông tin từ các bước thời gian trước đó thông qua trạng thái ẩn (Hidden State). Tuy nhiên, khi chuỗi dữ liệu trở nên dài, RNN 

39 

thường gặp hiện tượng mất gradient (Vanishing Gradient Problem), khiến mô hình khó ghi nhớ thông tin từ các thời điểm xa trong quá khứ. 

LSTM được đề xuất nhằm khắc phục vấn đề này bằng cách bổ sung cơ chế bộ nhớ (Memory Cell) và hệ thống các cổng điều khiển (Gate Mechanism). Các cổng này giúp mô hình lựa chọn thông tin cần ghi nhớ, loại bỏ hoặc sử dụng trong quá trình dự đoán. 

Trong đề tài này, dữ liệu chất lượng nước được thu thập liên tục theo thời gian, do đó các giá trị hiện tại có mối quan hệ với các giá trị trước đó. Ví dụ, nhiệt độ nước hoặc chỉ số pH tại thời điểm hiện tại có thể chịu ảnh hưởng bởi xu hướng biến đổi trong nhiều khoảng thời gian trước. Vì vậy, mô hình LSTM phù hợp để học và dự đoán sự thay đổi của các chỉ số chất lượng nước. 

## **3.4.2. Cấu trúc của mạng LSTM** 

Một tế bào LSTM (LSTM Cell) bao gồm các thành phần chính: 

- Cell State (Trạng thái bộ nhớ) 

- Hidden State (Trạng thái ẩn) 

- Forget Gate (Cổng quên) 

- Input Gate (Cổng đầu vào) 

- Output Gate (Cổng đầu ra) 

Cấu trúc hoạt động của LSTM: 

**Hình 3.1:** _Cấu trúc của mạng LSTM_ 

Trong đó: 

40 

- Xt: dữ liệu đầu vào tại thời điểm t 

- ht: trạng thái ẩn tại thời điểm t 

- Ct: trạng thái bộ nhớ tại thời điểm t 

## **3.4.3. Nguyên lý hoạt động của LSTM** 

LSTM hoạt động dựa trên cơ chế điều khiển thông tin thông qua ba cổng chính. 

## _a. Forget Gate (Cổng quên)_ 

Cổng quên quyết định thông tin nào từ bộ nhớ trước đó sẽ được giữ lại hoặc loại bỏ. 

**==> picture [119 x 16] intentionally omitted <==**

Trong đó: 

- 𝑓𝑡: đầu ra của cổng quên 

- 𝑊𝑓: ma trận trọng số 

**==> picture [91 x 17] intentionally omitted <==**

- 𝜎: hàm sigmoid 

Nếu giá trị đầu ra gần: 

**==> picture [147 x 13] intentionally omitted <==**

- 1 → thông tin được giữ lại 

## _b. Input Gate (Cổng đầu vào)_ 

Cổng đầu vào xác định thông tin mới cần được thêm vào bộ nhớ. 

**==> picture [116 x 15] intentionally omitted <==**

Thông tin mới được tạo: 

**==> picture [140 x 16] intentionally omitted <==**

Sau đó cập nhật trạng thái bộ nhớ: 

**==> picture [120 x 14] intentionally omitted <==**

## _c. Output Gate (Cổng đầu ra)_ 

Cổng đầu ra quyết định thông tin nào được đưa ra làm kết quả. 

**==> picture [127 x 33] intentionally omitted <==**

Trạng thái ẩn được tính: 

ℎ𝑡 = 𝑜𝑡 ×  𝑡𝑎𝑛ℎ(𝐶𝑡) 

## **3.4.4. Ưu điểm của LSTM** 

LSTM có một số ưu điểm nổi bật: 

- Có khả năng học dữ liệu chuỗi thời gian hiệu quả 

- Ghi nhớ được thông tin trong khoảng thời gian dài 

- Giảm hiện tượng mất gradient 

- Thích hợp với dữ liệu có tính phụ thuộc theo thời gian 

- Hoạt động tốt với dữ liệu cảm biến IoT 

## **3.4.5. Hạn chế của LSTM** 

Ngoài các ưu điểm, LSTM vẫn tồn tại một số hạn chế: 

- Thời gian huấn luyện tương đối dài 

- Số lượng tham số lớn 

- Cần dữ liệu đủ lớn để đạt hiệu quả cao 

- Tiêu tốn tài nguyên tính toán nhiều hơn các mô hình truyền thống 

## **3.4.6. Lý do lựa chọn LSTM cho đề tài** 

Đề tài sử dụng dữ liệu cảm biến chất lượng nước gồm: 

- water_pH 

- TDS 

- water_temp 

Các dữ liệu này có đặc điểm: 

- Thu thập liên tục theo thời gian 

- Có tính phụ thuộc giữa các thời điểm 

- Có xu hướng thay đổi theo chu kỳ hoặc xu hướng dài hạn 

Do đó, mô hình LSTM được lựa chọn vì có khả năng học và khai thác mối quan hệ thời gian tốt hơn so với các thuật toán truyền thống như Linear Regression hoặc Decision Tree. 

42 

## **3.5. Xây dựng mô hình LSTM** 

## **Code :** 

## `class LSTM(nn.Module):` 

```
def__init__(self, input_size=3, hidden_size=64, num_layers=2, output_size=3,
dropout=0.2):
super(LSTM, self).__init__()
self.hidden_size = hidden_size
self.num_layers = num_layers
# LSTM Layer
self.lstm = nn.LSTM(
input_size=input_size,
hidden_size=hidden_size,
num_layers=num_layers,
batch_first=True,
dropout=dropout if num_layers > 1else0.0
        )
# Fully connected layers to output predictions
self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_size)
        )
defforward(self, x):
            h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
            out, _ = self.lstm(x, (h0, c0))
            out_last = out[:, -1, :]
            prediction = self.fc(out_last)
return prediction
```

43 

**Hình 3.2:** _Mô hình LSTM_ 

## Giải thích: 

|**Layer**|**Tham số**|**Kích thước đầu**<br>**ra**|**Chức năng**|
|---|---|---|---|
|Input Layer|input_size = 3|(batch_size,<br>sequence_length,<br>3)|Nhận dữ liệu đầu vào gồm 3 đặc<br>trưng:water_pH,TDS,<br>water_temp. Dữ liệu được tổ<br>chức dưới dạng chuỗi thời gian<br>để mô hình học xu hướng biến<br>đổi theo thời gian.|
|LSTM<br>Layer|hidden_size =<br>64 num_layers<br>= 2|(batch_size,<br>sequence_length,<br>64)|Trích xuất đặc trưng theo thời<br>gian và học mối quan hệ giữa các<br>điểm dữ liệu liên tiếp. Mạng<br>LSTM có khả năng ghi nhớ<br>thông tin dài hạn, giúp dự đoán<br>xu hướng biến đổi của các chỉ số<br>chất lượng nước.|



44 

|||||
|---|---|---|---|
|Dropout<br>(trong<br>LSTM)|dropout = 0.2|Không thay đổi<br>kích thước|Vô hiệu hóa ngẫu nhiên 20% số<br>kết nối giữa các lớp LSTM trong<br>quá trình huấn luyện nhằm giảm<br>hiện tượng overfitting và tăng<br>khả năng tổng quát hóa của mô<br>hình.|
|Fully<br>Connected<br>Layer 1|Linear(64 →<br>32)|(batch_size, 32)|Chuyển đổi đầu ra của LSTM<br>sang không gian đặc trưng nhỏ<br>hơn, đồng thời tổng hợp các đặc<br>trưng đã học được từ chuỗi thời<br>gian.|
|ReLU<br>Activation|ReLU()|(batch_size, 32)|Áp dụng hàm kích hoạt phi tuyến<br>để tăng khả năng học các mối<br>quan hệ phức tạp giữa các đặc<br>trưng. Đồng thời giúp giảm hiện<br>tượng gradient biến mất.|
|Dropout<br>Layer|Dropout(0.2)|(batch_size, 32)|Loại bỏ ngẫu nhiên một số<br>neuron trong quá trình huấn<br>luyện nhằm hạn chế mô hình ghi<br>nhớ quá mức dữ liệu huấn luyện.|
|Output<br>Layer|Linear(32 →<br>3)|(batch_size, 3)|Sinh ra kết quả dự đoán gồm 3<br>giá trị đầu ra:water_pH,TDS,<br>water_temptại thời điểm tương<br>lai.|



## **3.6. Huấn luyện mô hình** 

## **3.6.1. Chia dữ liệu** 

Dữ liệu được chia thành: 

|Dữ liệu được chia thành:||
|---|---|
|||
|**Tập dữ liệu**|**Tỷ lệ**|
|Training|70%|



45 

|||
|---|---|
|Validation|15%|
|Testing|15%|



## Mục đích: 

- Training: học mô hình 

- Validation: điều chỉnh tham số 

- Testing: đánh giá 

## **3.6.2. Tham số huấn luyện** 

|**3.6.2. Tham số huấn luyện**||
|---|---|
|**Tham số**|**Giá trị**|
|Epoch|100|
|Batch size|32|
|Learning rate|0.001|
|Optimizer|Adam|
|Loss Function|MSE|



## **Hàm mất mát MSE:** 

**==> picture [144 x 42] intentionally omitted <==**

Giải thích: 

- n: số lượng mẫu 

- 𝑦𝑖: giá trị thực tế 

- ŷ𝑖: giá trị dự đoán 

- (𝑦𝑖 − ŷ𝑖)[2] : bình phương sai số 

Mô tả: MSE là trung bình bình phương sai số giữa giá trị dự đoán và giá trị thực tế. Việc bình phương sai số giúp mô hình phạt mạnh hơn đối với các sai số lớn. 

46 

## **3.7. Đánh giá mô hình** 

## **3.7.1. Các chỉ số đánh giá** 

- _a. MAE: Phản ánh sai số tuyệt đối trung bình._ 

**==> picture [122 x 39] intentionally omitted <==**

## **Giải thích:** 

- n: số lượng mẫu dữ liệu 

- 𝑦𝑖: giá trị thực tế 

- ŷ𝑖: giá trị dự đoán 

- |𝑦𝑖 −𝑦̂𝑖|:sai số tuyệt đối 

Mô tả: MAE là giá trị trung bình của sai số tuyệt đối giữa giá trị dự đoán và giá trị thực tế. Chỉ số này phản ánh mức sai lệch trung bình của mô hình mà không xét đến hướng sai lệch. 

## _b. RMSE: Phản ánh độ lệch giữa giá trị dự đoán và thực tế._ 

**==> picture [168 x 54] intentionally omitted <==**

Giải thích: 

- n: số lượng mẫu 

- 𝑦𝑖: giá trị thực tế 

- ŷ𝑖: giá trị dự đoán 

Mô tả: RMSE là căn bậc hai của MSE. Chỉ số này có cùng đơn vị với dữ liệu đầu vào nên dễ diễn giải và đánh giá hơn so với MSE. 

## **3.7.2. Kết quả thực nghiệm** 

Ví dụ: 

|Ví dụ:|||
|---|---|---|
|**Chỉ số**|**MAE**|**RMSE**|
|pH|0.15|0.21|
|TDS|3.4|4.1|



47 

Temperature 0.25 0.31 

## **3.7.3. Biểu đồ đánh giá** 

Các biểu đồ cần trình bày: 

- **Biểu đồ Loss** 

**Hình 3.3:** _Biểu đồ Loss_ 

##  **Biểu đồ giá trị dự đoán** 

**==> picture [17 x 10] intentionally omitted <==**

**----- Start of picture text -----**<br>
48<br>**----- End of picture text -----**<br>


**Hình 3.4:** _Biểu đồ giá trị dự đoán_ 

## **3.8. Tích hợp AI Service vào hệ thống** 

## **3.8.1. Kiến trúc AI Service** 

**Hình 3.5:** _Kiến trúc AI Service_ 

## **3.8.2. Quy trình hoạt động** 

- **Bước 1:** Cảm biến thu thập dữ liệu. 

- **Bước 2:** Dữ liệu gửi đến Backend. 

- **Bước 3:** Backend lưu vào cơ sở dữ liệu. 

- **Bước 4:** AI Service lấy dữ liệu gần nhất. 

- **Bước 5:** Tiền xử lý dữ liệu. 

- **Bước 6:** Mô hình dự đoán giá trị tương lai. 

- **Bước 7:** Kết quả trả về Frontend. 

49 

## **3.8.3. Thiết kế API** 

## **Request: POST /predict:** 

**Body:** { "history": [ {"water_pH": 7.2, "TDS": 315.0, "water_temp": 26.1}, {"water_pH": 7.1, "TDS": 316.0, "water_temp": 26.0}, {"water_pH": 7.1, "TDS": 318.0, "water_temp": 25.9}, // ... (tổng cộng đủ 24 bản ghi của 24 giờ liên tục gần nhất) ... {"water_pH": 6.9, "TDS": 325.0, "water_temp": 25.6} ] } 

**Response:** 

{ "predicted_pH":6.8, "predicted_TDS":327, "predicted_temp":25.4 } 

50 

## **CHƯƠNG 4: KẾT QUẢ** 

## **4.1. Kết quả phần mềm** 

Giao diện dashboard của hệ thống được xây dựng theo hướng trực quan và thân thiện với người dùng, cho phép giám sát toàn bộ trạng thái môi trường nuôi trồng thủy sản theo thời gian thực. Dashboard hiển thị các thông số quan trọng như nồng độ oxy hòa tan (O₂), độ pH, nồng độ amoniac (NH₃), nhiệt độ nước, tổng chất rắn hòa tan (TDS), độ đục và mực nước dưới dạng các thẻ thông tin riêng biệt. Mỗi thông số đều được hiển thị kèm trạng thái đánh giá như “Bình thường”, “Nguy hiểm” hoặc “Ổn định”, giúp người dùng nhanh chóng nhận biết tình trạng hiện tại của môi trường nuôi. 

**Hình 4.1:** _Giao diện bảng điều khiển_ 

51 

Ngoài việc hiển thị dữ liệu tức thời, hệ thống còn hỗ trợ biểu diễn dữ liệu dưới dạng biểu đồ theo thời gian, giúp người dùng dễ dàng theo dõi xu hướng thay đổi của các thông số môi trường (O₂, NH₃, pH và nhiệt độ nước). Phần điều khiển thiết bị được thiết kế rõ ràng và dễ thao tác, hỗ trợ quản lý các thiết bị như hệ thống sục khí, bơm xả nước, bơm cấp nước và cơ chế cho ăn tự động. Người dùng có thể lựa chọn giữa chế độ tự động hoặc điều khiển thủ công tùy theo nhu cầu sử dụng. 

Bên cạnh đó, dashboard còn tích hợp khu vực nhật ký cảnh báo nhằm lưu lại các sự kiện quan trọng như nồng độ NH₃ tăng cao, oxy giảm thấp hoặc hệ thống kích hoạt bơm tự động. Điều này giúp người dùng dễ dàng theo dõi lịch sử hoạt động và đánh giá mức độ ổn định của môi trường nuôi theo thời gian. 

Tổng thể, dashboard đóng vai trò là trung tâm giám sát và điều khiển của hệ thống, giúp kết nối dữ liệu từ ESP32 với người dùng thông qua giao diện web hiện đại, hỗ trợ quá trình quản lý môi trường nuôi trồng thủy sản một cách thuận tiện và hiệu quả hơn. 

## **4.2. Kết quả phần cứng** 

Phần cứng được lắp đặt theo đúng sơ đồ thiết kế, ESP32 có khả năng thu thập dữ liệu từ các cảm biến môi trường như O₂, pH, NH₃, nhiệt độ, mực nước, TDS và độ đục nước. Hệ thống có thể điều khiển các thiết bị ngoại vi như máy bơm nước, hệ thống sục khí và cơ chế cho ăn (được mô phỏng bằng relay và đèn LED) dựa trên lệnh từ người dùng hoặc theo cơ chế điều khiển tự động. ESP32 đồng thời hỗ trợ gửi dữ liệu cảm biến theo thời gian thực lên web dashboard thông qua kết nối WiFi, giúp người dùng giám sát trạng thái môi trường và thiết bị từ xa một cách thuận tiện. 

**Hình 4.2:** _Kết quả lắp mạch thực tế_ 

52 

## **KẾT LUẬN** 

Dự án Hệ thống giám sát và điều khiển môi trường nuôi trồng thủy sản đã hoàn thành các mục tiêu đề ra, bao gồm xây dựng được nền tảng giám sát và điều khiển các thiết bị môi trường thông qua vi điều khiển ESP32 và giao diện web dashboard. Hệ thống cho phép theo dõi liên tục các thông số quan trọng của môi trường nuôi như nồng độ oxy hòa tan (O₂), độ pH, nồng độ amoniac (NH₃), nhiệt độ nước, mực nước, độ đục và tổng chất rắn hòa tan (TDS). Đồng thời, hệ thống hỗ trợ điều khiển các thiết bị như máy bơm nước, hệ thống sục khí và cơ chế cho ăn theo thời gian thực. Giao diện giám sát được xây dựng theo hướng trực quan, hỗ trợ hiển thị dữ liệu dưới dạng biểu đồ và trạng thái hoạt động của thiết bị, giúp người dùng dễ dàng theo dõi và quản lý môi trường nuôi từ xa. Qua quá trình triển khai và thử nghiệm, hệ thống đã hoạt động ổn định và đáp ứng được các chức năng cốt lõi của một mô hình nuôi trồng thủy sản thông minh quy mô nhỏ. 

Tuy nhiên, dự án vẫn còn một số hạn chế nhất định. Một số cảm biến trong hệ thống hiện vẫn được mô phỏng bằng biến trở nên độ chính xác chưa phản ánh hoàn toàn điều kiện thực tế của môi trường nuôi. Cảm biến đo mực nước HC-SR04 có thể bị ảnh hưởng bởi dao động mặt nước và chưa phù hợp với môi trường ngoài trời trong thời gian dài. Ngoài ra, hệ thống hiện mới tập trung vào mô hình nuôi thủy sản quy mô nhỏ nên chưa hỗ trợ đầy đủ các thông số chuyên sâu cho từng loại thủy sản như tôm hoặc cá nước mặn. Các cơ chế điều khiển tự động hiện chủ yếu dựa trên ngưỡng cố định và chưa áp dụng các thuật toán tối ưu hoặc phân tích dữ liệu thông minh. 

Trong tương lai, dự án sẽ được mở rộng theo hướng sử dụng các cảm biến thực tế có độ chính xác cao hơn, tích hợp thêm các thông số môi trường chuyên sâu như độ mặn hoặc NO₂, đồng thời nâng cấp hệ thống điều khiển tự động theo hướng thông minh và linh hoạt hơn. Bên cạnh đó, hệ thống có thể được phát triển theo kiến trúc module nhằm hỗ trợ mở rộng thêm cảm biến và thiết bị mà không cần thay đổi toàn bộ hệ thống, hướng tới một nền tảng giám sát và điều khiển nuôi trồng thủy sản toàn diện, ổn định và phù hợp với thực tế hơn. 

53 

## **TÀI LIỆU THAM KHẢO** 

[1] https://fastapi.tiangolo.com 

[2] https://mqtt.org 

[3] https://docs.espressif.com/projects/arduino-esp32 

54 

