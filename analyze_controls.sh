
for file_ui in $( git ls-files -- "*.ui" ); do
    file_qs1="${file_ui%\.*}.qs"
    file_qs="${file_qs1/forms/scripts}"
    

    test -f "$file_qs" && {
        for control in $(grep -Po "this\.child\(.(\w+).\)" "$file_qs" | sort -u | sed "s/\"/\t/g" | awk '{print $2}'); do
            grep -Eq "<cstring>$control" "$file_ui" || echo $file_qs $control; 
        done
    } || echo "ERROR: $file_qs"
    
done
