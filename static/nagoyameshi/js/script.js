//DjangoMessageFrameWorkの削除機能
const notify_deletes    = document.querySelectorAll(".notify_message_delete");
for (let notify_delete of notify_deletes ){
    // クリックされたとき、その要素の親要素.notify_messageを削除する。
    notify_delete.addEventListener("click", (event) => {
        event.currentTarget.closest(".notify_message").remove();
    });
}

//5秒経ったら自動的に消す
setTimeout( () => {
    const messages  = document.querySelectorAll(".notify_message");
    for (let message of messages){
        message.remove();
    }
}, 5000);