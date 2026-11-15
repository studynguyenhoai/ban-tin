# Weha · Bản tin sáng — quy trình chạy tự động (cập nhật 11/11/2026)

Bản tin 2 trang A4 cho Nguyễn Hoài (Weha · 0396 336 096), thứ 2–6. Kết quả cuối là MỘT file PNG < 5 MB, đẩy lên GitHub `studynguyenhoai/ban-tin` (nhánh main) tại `bantin/YYYY-MM-DD.png`; n8n lấy ảnh từ đó gửi Zalo. KHÔNG gửi ảnh trực tiếp cho người dùng.
Script dựng hình: `claude/weha/weha_sang.py` (logo nhúng sẵn, tự ghép 2 trang thành 1 PNG). Dữ liệu mẫu: `claude/weha/vi_du_du_lieu.json`.

## QUY TẮC TIẾT KIỆM TOKEN (bắt buộc)
1. Lấy script bằng ĐÚNG MỘT lần `project_read` rồi Write ra file; không Read lại, không in dòng `LOGO = "..."`, không Read file có base64 hay file artifact.
2. Không viết lại script hay mã ghép ảnh: script đã tự ghép ra `out/YYYY-MM-DD.png` và in kích thước.
3. Chỉ đọc 2 doc: file hướng dẫn này và `vi_du_du_lieu.json`. Không đọc doc khác.
4. Tin tức: mỗi nhóm (quốc tế, trong nước, doanh nghiệp) gọi tối đa 2 lần, 5–8 tin/lần; đủ dữ liệu thì dừng, không gọi lại.
5. Bỏ qua nguồn lỗi/hết credit (Bigdata.com, Algolab): thử đúng 1 lần, lỗi thì chuyển sang WiData, không thử lại.
6. Chỉ xem ảnh 1 lần ở bản cuối (hoặc chỉ dựa vào chiều cao/hệ số chữ script in ra).
7. Kiểm tra `test -n "$WEHA_GH_TOKEN"` ngay từ đầu; nếu "khong" thì làm bản tin nhưng báo thiếu token ngay ở bước báo cáo, không tốn lượt thử cách khác.

## Quy trình
1. Ngày = hôm nay giờ Việt Nam; phiên trước = phiên HOSE gần nhất. Ngày nghỉ lễ sàn thì không làm, chỉ báo ngắn.
2. Thu thập dữ liệu (song song): phiên trước (VN-Index, VN30, khối ngoại, tự doanh), quốc tế, trong nước, doanh nghiệp, cổ tức & quyền, sự kiện (WiData là nguồn chính: wi_data_stock, wi_data_macro, wi_data_commodity, wi_data_news, wi_data_companies). Số lấy từ công cụ trong lần chạy này, không đoán; thiếu thì bỏ ô/tin.
3. Viết JSON theo cấu trúc file mẫu: headline ≤ 25 chữ (số chính trong `<mark>`), lede 1 câu, strip 4 ô, intl_tiles 5, dom_tiles 5 (nhãn ≤ 16 ký tự, giá trị ngắn để không xuống dòng), intl_news 4, dom_news 5, company_news 7 (`s` = "+", "-", "o"), dividends ≤ 12 dòng, events ≤ 10 dòng. Số kiểu Việt Nam, dấu trừ "−". KHÔNG ghi nguồn.
4. Chạy `python3 weha_sang.py du_lieu.json out`. Nếu "CẢNH BÁO … tràn" thì bớt 1 tin rồi chạy lại. Ảnh cuối: `out/YYYY-MM-DD.png` (phải < 5.000.000 byte).
5. Đẩy GitHub: `git clone` repo (có token: dùng `-c http.extraHeader` Basic auth; không in token, không ghi token vào file/commit/remote URL), copy ảnh vào `bantin/YYYY-MM-DD.png`, chỉ `git add` đúng file đó, commit "Bản tin YYYY-MM-DD", push main (bị từ chối thì `git pull --rebase` rồi push 1 lần; không force push). Kiểm tra `git log -1 --stat`.
6. Báo bằng PushNotification (proactive, trong `<routine_summary>`): thành công thì câu đầu "Bản tin sáng dd/mm/yyyy đã đẩy lên GitHub", kèm link `https://github.com/studynguyenhoai/ban-tin/blob/main/bantin/YYYY-MM-DD.png` và dung lượng; lỗi thì nói rõ lỗi gì, ảnh đã dựng chưa, cần làm gì. Dữ liệu thiếu thì nói nguồn nào lỗi và không đẩy ảnh dở dang.
