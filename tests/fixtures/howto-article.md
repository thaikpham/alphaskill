# Khi nào AWB sai, và cách chọn White Balance đúng

Khi nào AWB thất bại và bạn cần White Balance thủ công. Danh sách WB preset, cách đo Daylight, và mẹo để không bị xanh hay vàng.

**TL;DR**

- AWB (Auto White Balance) chọn dựa trên trung bình ánh sáng khung; nó sai khi có một màu ánh sáng chiếm ưu thế.
- Ba tình huống: đèn huỳnh quang (xanh lạnh), lửa hay đèn sợi (cam nóng), hoặc vật quá sáng/tối làm nhiễu.
- Ba công cụ sửa: preset (Daylight, Incandescent, bốn mức Fluor.), chọn Kelvin tay, hoặc chỉnh Shift A/B.

Cân bằng trắng và nhiệt độ màu là cách máy diễn dịch màu sắc ánh sáng khi chụp. Khi máy chọn AWB (tự động), nó tìm điểm trung lập rồi cân bằng. Nhưng ba tình huống khiến nó sai: ánh sáng có tên (đèn huỳnh quang xanh lạnh, lửa cam nóng), hoặc ảnh có vật quá sáng hay quá tối làm nhầm lạc máy.

![Chụp dưới ánh sáng hỗn hợp: AWB chọn trung bình dẫn đến màu sắc bị lệch. Ảnh: CoolKoon · CC BY-SA 4.0 · Wikimedia Commons](/blog/khi-nao-roi-awb-2.jpg)

## Ba tình huống AWB nhầm lẫn

Đèn huỳnh quang ám xanh lục khiến da người xỉn. Lửa hay đèn sợi đốt rất cam, máy bù xanh để cân lại và làm mất hơi ấm tự nhiên. Khi ảnh có vật rất sáng (tường trắng) hoặc rất tối (nền đen), máy sẽ điều chỉnh cho nó thành trung tính, làm phần còn lại bị ảnh hưởng.

## Ba công cụ chọn White Balance tay

Sony cung cấp ba cách để bạn cài đặt cân bằng trắng thủ công, tùy theo tình huống và mức độ chính xác bạn cần.

| Công cụ | Cách dùng | Khi nào tốt |
| --- | --- | --- |
| Preset | Chọn Daylight, Fluor., Incandescent từ menu WB | Ánh sáng có tên rõ |
| Kelvin (C.Temp.) | Nhập nhiệt độ từ 2500–9900K | Bạn biết chính xác nhiệt độ |
| Tuning (Shift A/B) | Điều chỉnh mũi tên theo hướng Amber (ấm) hoặc Blue (lạnh) | Tinh chỉnh sau Preset |

Công cụ sửa

## Gray Card: công cụ chính xác nhất

Gray Card là tờ giấy xám 18% được làm để phản chiếu ánh sáng trung tính. Chụp Gray Card dưới ánh sáng bạn sắp dùng, rồi đo Custom White Balance từ tấm đó, hoặc chỉnh ảnh sau trong Lightroom. Nó là cách chính xác nhất khi ánh sáng không có Preset rõ ràng.

## RAW và JPEG

RAW lưu dữ liệu gốc mà không áp dụng White Balance khi chụp. Bạn chỉnh màu sau trong Lightroom hay Imaging Edge khi thấy đầy đủ dữ liệu và dễ khôi phục hơn. White Balance chỉ là tham khảo trong metadata. Ngược lại, JPEG được máy xử lý ngay khi chụp nên White Balance quyết định màu sắc cuối cùng.

**Chọn White Balance tay**
- [ ] Chụp một tấm với AWB để thấy màu sắc hiện tại.
- [ ] Nhận dạng ánh sáng: Daylight, Incandescent hay một mức Fluor.
- [ ] Chọn Preset trong menu White Balance.
- [ ] Chụp lại và so sánh với tấm AWB.
- [ ] Nếu chưa tốt, chỉnh Shift A/B thêm Amber hoặc Blue.
- [ ] Tắt menu để lưu cấu hình.

## Câu hỏi thường gặp

### AWB (Auto White Balance) sai như thế nào là thường gặp nhất?

AWB hay bị xanh lạnh ở dưới bóng tre, ngoài nắng trong nhà, hoặc khi một nửa khung ánh sáng nắng vàng nửa ánh sáng bóng xanh (chế độ Ambience sẽ chọn sai). Cách nhận biết: ảnh trông lạnh hơn thực tế hoặc ấm hơn thực tế so với mắt. Kiểm tra bằng White Balance Bracket hoặc Custom WB.

### Khi nào nên dùng Custom White Balance thay vì AWB?

Khi ánh sáng là nguồn duy nhất, ổn định (một màn hình LED, một ngọn đèn halogen) và AWB không đoán đúng. Cách làm: chụp thẻ trắng hoặc một vật màu trung tính dưới ánh sáng đó, vào menu WB → Set., chọn ảnh đó. Sau đó tất cả ảnh sẽ dùng WB thẻ đó.

### Fluor. (Bóng Huỳnh quang) có khác Daylight (Nắng) không?

Có, rất khác. Daylight (khoảng 5500K) cho ánh sáng trung tính. Fluor. phụ thuộc loại bóng (trắng lạnh 5000K, trắng ấm 2700K). máy Sony thường mặc định Fluor. = bóng lạnh. Ở phòng làm việc bóng trắng, dùng Fluor. hoặc +A (Ambience mode) sẽ ấm hơn. Chọn cái nào tùy gu, không có cái nào sai hoàn toàn.

### Tại sao C.Temp./Filter lại có tới 126 bước từ 2500K đến 9900K?

Vì không phải lúc nào bạn cũng muốn màu trung tính (5500K). Chụp ở chiều hoàng hôn vàng (3000K) hay dưới ánh trăng xanh (8000K+) là bình thường. C.Temp./Filter cho bạn chọn chính xác màu bạn muốn từ menu, thay vì phải dự đoán tên preset Daylight/Cloudy/Shade là gần đúng.

### Priority Set in AWB là mục gì?

Là cách bảo máy ưu tiên loại ánh sáng nào khi chọn WB tự động. Có hai lựa chọn: Ambience (ưu tiên xanh lạnh khi chong chóng dưới bóng) hoặc White Preservation (ưu tiên trung tính, giữ vật trắng là trắng). Lựa chọn không ảnh hưởng nếu bạn chọn WB cụ thể (Daylight, Custom, v.v.)

### Có cách nào nhanh chóng chọn WB mà không cần vào menu không?

Có, gán White Balance vào Custom Key hoặc Control Wheel. Vào menu Custom Key, chọn nút nào đó, gán "White Balance" vào nó. Sau đó nhấn nút đó sẽ hiển thị danh sách WB ở màn hình, bạn chọn bằng phím mũi tên. Nhanh hơn vào MENU từng lần.
