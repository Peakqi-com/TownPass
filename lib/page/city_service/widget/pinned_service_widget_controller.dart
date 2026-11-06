import 'package:get/get.dart';
import 'package:town_pass/page/city_service/model/my_service_model.dart';

class PinnedServiceWidgetController extends GetxController {
  final RxList<MyServiceItemId> _pinnedList = RxList(
    [
      MyServiceItemId.locationSearch,
      MyServiceItemId.districtOffice,
      MyServiceItemId.dashboard,
      // 置頂清單只存在記憶體，App 重啟會回到這份預設清單；放在這裡讓 Demo 一打開就看得到
      MyServiceItemId.peakqiService,
    ],
  );

  RxList<MyServiceItemId> get pinnedList => _pinnedList;

  bool remove(MyServiceItemId itemId) {
    return _pinnedList.remove(itemId);
  }

  bool replaceWith(List<MyServiceItemId> list) {
    if (list.isNotEmpty) {
      _pinnedList.value = list;
      return true;
    }
    return false;
  }

  bool push(MyServiceItemId itemId) {
    if (_pinnedList.length < 12) {
      _pinnedList.add(itemId);
      return true;
    }
    return false;
  }
}
